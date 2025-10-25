from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from django.db import transaction
from decimal import Decimal
#import requests
import os
import random
import string
from datetime import timedelta

from ..models import (
    Payment,
    PaymentStatusHistory,
    Refund,
    PENDING,
    PROCESSING,
    APPROVED,
    DECLINED,
    REFUNDED,
    CANCELLED,
    CREDIT_CARD,
    DEBIT_CARD,
    PIX,
    BOLETO,
)
from ..serializers import (
    PaymentListSerializer,
    PaymentDetailSerializer,
    PaymentCreateSerializer,
    PaymentUpdateStatusSerializer,
    RefundRequestSerializer,
)




class IsAuthenticatedOrAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        if hasattr(request.user, 'is_admin') and (request.user.is_admin or request.user.is_admin_master):
            return True
        
        return obj.user_id == request.user.id


class PaymentViewSet(viewsets.ModelViewSet): 
    queryset = Payment.objects.prefetch_related('status_history', 'refunds')
    permission_classes = [IsAuthenticatedOrAdmin]
    
    def get_serializer_class(self):
        if self.action == 'list':
            return PaymentListSerializer
        elif self.action == 'create':
            return PaymentCreateSerializer
        return PaymentDetailSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        
        if hasattr(user, 'is_admin') and (user.is_admin or user.is_admin_master):
            return queryset
        
        return queryset.filter(user_id=user.id)
    
    def list(self, request):
        queryset = self.get_queryset()
        status_filter = request.query_params.get('status')
        payment_method = request.query_params.get('payment_method')
        order_id = request.query_params.get('order_id')
        
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        if payment_method:
            queryset = queryset.filter(payment_method=payment_method)
        
        if order_id:
            queryset = queryset.filter(order_id=order_id)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @transaction.atomic
    def create(self, request):
        serializer = PaymentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = request.user
        order_id = serializer.validated_data['order_id']
        payment_method = serializer.validated_data['payment_method']
        
        try:
            order_data = self._get_order_data(order_id, user.id)
            
            if not order_data:
                return Response({
                    'error': 'Pedido não encontrado.'
                }, status=status.HTTP_404_NOT_FOUND)
            
            existing_payment = Payment.objects.filter(
                order_id=order_id,
                status=APPROVED
            ).first()
            
            if existing_payment:
                return Response({
                    'error': 'Este pedido já possui um pagamento aprovado.'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            payment = Payment.objects.create(
                order_id=order_id,
                user_id=user.id,
                user_name=user.name,
                user_email=user.email,
                payment_method=payment_method,
                status=PENDING,
                amount=Decimal(str(order_data['total']))
            )
            
            if payment_method in [CREDIT_CARD, DEBIT_CARD]:
                self._process_card_payment(payment, serializer.validated_data)
            elif payment_method == PIX:
                self._process_pix_payment(payment, serializer.validated_data)
            elif payment_method == BOLETO:
                self._process_boleto_payment(payment)
            
            PaymentStatusHistory.objects.create(
                payment=payment,
                from_status=PENDING,
                to_status=payment.status,
                comment='Pagamento criado',
                changed_by=user.id
            )
            
            if payment.status == APPROVED:
                self._update_order_status(order_id, 'confirmed')
            
            return Response({
                'message': 'Pagamento processado com sucesso!',
                'payment': PaymentDetailSerializer(payment).data
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response({
                'error': f'Erro ao processar pagamento: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def retrieve(self, request, pk=None):
        payment = self.get_object()
        serializer = self.get_serializer(payment)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        if not (hasattr(request.user, 'is_admin') and 
                (request.user.is_admin or request.user.is_admin_master)):
            return Response(
                {'error': 'Apenas administradores podem atualizar status.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        payment = self.get_object()
        serializer = PaymentUpdateStatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        new_status = serializer.validated_data['status']
        comment = serializer.validated_data.get('comment', '')
        decline_reason = serializer.validated_data.get('decline_reason', '')
        old_status = payment.status
        payment.status = new_status
        
        if new_status == PROCESSING:
            payment.processed_at = timezone.now()
        elif new_status == APPROVED:
            payment.approved_at = timezone.now()
            self._update_order_status(payment.order_id, 'confirmed')
        elif new_status == DECLINED:
            payment.decline_reason = decline_reason
        
        payment.save()
        
        PaymentStatusHistory.objects.create(
            payment=payment,
            from_status=old_status,
            to_status=new_status,
            comment=comment,
            changed_by=request.user.id
        )
        
        return Response({
            'message': 'Status atualizado com sucesso!',
            'payment': PaymentDetailSerializer(payment).data
        })
    
    @action(detail=True, methods=['post'])
    def request_refund(self, request, pk=None):
        payment = self.get_object()
        serializer = RefundRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        if not payment.can_be_refunded:
            return Response({
                'error': 'Este pagamento não pode ser reembolsado.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        refund_amount = serializer.validated_data.get('amount', payment.amount)
        
        if refund_amount > payment.amount:
            return Response({
                'error': 'Valor do reembolso maior que o valor pago.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        refund = Refund.objects.create(
            payment=payment,
            amount=refund_amount,
            reason=serializer.validated_data['reason'],
            requested_by=request.user.id
        )
        
        self._process_refund(refund)
        
        if refund.status == 'completed':
            old_status = payment.status
            payment.status = REFUNDED
            payment.refunded_at = timezone.now()
            payment.save()
            
            PaymentStatusHistory.objects.create(
                payment=payment,
                from_status=old_status,
                to_status=REFUNDED,
                comment=f'Reembolso processado: {serializer.validated_data["reason"]}',
                changed_by=request.user.id
            )
            
            self._update_order_status(payment.order_id, 'cancelled')
        
        return Response({
            'message': 'Reembolso solicitado com sucesso!',
            'refund': {
                'id': str(refund.id),
                'amount': str(refund.amount),
                'status': refund.status,
                'created_at': refund.created_at
            }
        })
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        if not (hasattr(request.user, 'is_admin') and 
                (request.user.is_admin or request.user.is_admin_master)):
            return Response(
                {'error': 'Apenas administradores podem ver estatísticas.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        queryset = Payment.objects.all()
        
        stats = {
            'total_payments': queryset.count(),
            'pending': queryset.filter(status=PENDING).count(),
            'processing': queryset.filter(status=PROCESSING).count(),
            'approved': queryset.filter(status=APPROVED).count(),
            'declined': queryset.filter(status=DECLINED).count(),
            'refunded': queryset.filter(status=REFUNDED).count(),
            'total_amount': sum(
                payment.amount for payment in queryset.filter(status=APPROVED)
            ),
            'by_method': {
                'credit_card': queryset.filter(payment_method=CREDIT_CARD).count(),
                'debit_card': queryset.filter(payment_method=DEBIT_CARD).count(),
                'pix': queryset.filter(payment_method=PIX).count(),
                'boleto': queryset.filter(payment_method=BOLETO).count(),
            }
        }
        
        return Response(stats)
    
    def _get_order_data(self, order_id, user_id):
        orders_url = os.getenv('ORDERS_SERVICE_URL', 'http://gestao-pedidos-service:8003')
        
        try:
            response = requests.get(
                f'{orders_url}/api/v1/orders/{order_id}/',
                timeout=5
            )
            
            if response.status_code == 200:
                return response.json()
        except:
            pass
        
        return None
    
    def _process_card_payment(self, payment, data):
        card_number = data['card_number'].replace(' ', '')
        payment.card_holder_name = data['card_holder_name']
        payment.card_number_last4 = card_number[-4:]
        payment.card_brand = self._get_card_brand(card_number)
        payment.installments = data.get('installments', 1)
        payment.status = PROCESSING
        payment.processed_at = timezone.now()
        
        if random.random() < 0.9:
            payment.status = APPROVED
            payment.approved_at = timezone.now()
            payment.gateway_transaction_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=16))
        else:
            payment.status = DECLINED
            payment.decline_reason = 'Transação não autorizada pela operadora'
        
        payment.save()
    
    def _process_pix_payment(self, payment, data):
        payment.pix_key = data.get('pix_key', 'pix@cherry.com.br')
        payment.pix_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=32))
        payment.status = PENDING
        payment.save()
    
    def _process_boleto_payment(self, payment):
        payment.boleto_barcode = ''.join(random.choices(string.digits, k=47))
        payment.boleto_url = f"https://boleto.cherry.com.br/{payment.id}"
        payment.boleto_due_date = (timezone.now() + timedelta(days=3)).date()
        payment.status = PENDING
        payment.save()
    
    def _process_refund(self, refund):
        refund.status = 'processing'
        refund.save()
        refund.status = 'completed'
        refund.completed_at = timezone.now()
        refund.gateway_refund_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=16))
        refund.save()
    
    def _update_order_status(self, order_id, new_status):
        orders_url = os.getenv('ORDERS_SERVICE_URL', 'http://gestao-pedidos-service:8003')
        
        try:
            requests.post(
                f'{orders_url}/api/v1/orders/{order_id}/update-status/',
                json={'status': new_status},
                timeout=5
            )
        except:
            pass
    
    def _get_card_brand(self, card_number):
        first_digit = card_number[0]
        
        brands = {
            '4': 'Visa',
            '5': 'Mastercard',
            '3': 'Amex',
            '6': 'Discover'
        }
        
        return brands.get(first_digit, 'Unknown')
