from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import Q
from django.db.models import Count, Sum
from decimal import Decimal
import requests
import os

from ..models import (
    Order,
    OrderItem,
    OrderStatusHistory,
    PENDING,
    CONFIRMED,
    PROCESSING,
    SHIPPED,
    DELIVERED,
    CANCELLED,
)
from ..serializers import (
    OrderListSerializer,
    OrderDetailSerializer,
    OrderCreateSerializer,
    OrderUpdateStatusSerializer,
    OrderCancelSerializer,
)




class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.prefetch_related('items', 'status_history')
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'list':
            return OrderListSerializer
        elif self.action == 'create':
            return OrderCreateSerializer
        return OrderDetailSerializer
    
    def get_queryset(self):
        user = self.request.user
        queryset = super().get_queryset()
        
        if hasattr(user, 'is_admin') and (user.is_admin or user.is_admin_master):
            return queryset

        return queryset.filter(user_id=user.id)
    



    
    def list(self, request):
        queryset = self.get_queryset()
        status_filter = request.query_params.get('status')
        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')
        search = request.query_params.get('search')
        
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        if date_from:
            queryset = queryset.filter(created_at__gte=date_from)
        
        if date_to:
            queryset = queryset.filter(created_at__lte=date_to)
        
        if search:
            queryset = queryset.filter(
                Q(user_name__icontains=search) |
                Q(user_email__icontains=search) |
                Q(id__icontains=search)
            )
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = request.user
        
        user_data = {
            'user_id': user.id,
            'user_name': user.name,
            'user_email': user.email,
            'user_phone': getattr(user, 'phone', ''),
        }
        
        address_id = serializer.validated_data.get('address_id')
        if address_id:
            address_data = self._get_address(user.id, address_id, request)
            if not address_data:
                return Response(
                    {'error': 'Endereço não encontrado.'},
                    status=status.HTTP_404_NOT_FOUND
                )
        else:
            address_data = {
                'shipping_street': serializer.validated_data['shipping_street'],
                'shipping_number': serializer.validated_data['shipping_number'],
                'shipping_complement': serializer.validated_data.get('shipping_complement', ''),
                'shipping_neighborhood': serializer.validated_data['shipping_neighborhood'],
                'shipping_city': serializer.validated_data['shipping_city'],
                'shipping_state': serializer.validated_data['shipping_state'],
                'shipping_zip_code': serializer.validated_data['shipping_zip_code'],
            }
        
        items_data = serializer.validated_data['items']
        products_info = []
        subtotal = Decimal('0.00')

        for item_data in items_data:
            product = self._get_product(item_data['product_id'], request)
        
    
            if not product:
                return Response(
                    {'error': f'Produto {item_data["product_id"]} não encontrado.'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            if not product.get('is_in_stock') or product.get('stock', 0) < item_data['quantity']:
                return Response(
                    {'error': f'Produto "{product["name"]}" sem estoque suficiente.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            item_subtotal = Decimal(str(product['price'])) * item_data['quantity']
            subtotal += item_subtotal
            
            products_info.append({
                'product_id': product['id'],
                'product_name': product['name'],
                'product_sku': product.get('sku', ''),
                'product_image': product.get('main_image_url', ''),
                'quantity': item_data['quantity'],
                'unit_price': Decimal(str(product['price'])),
                'subtotal': item_subtotal,
            })
        
        shipping_cost = serializer.validated_data.get('shipping_cost', Decimal('0.00'))
        discount = serializer.validated_data.get('discount', Decimal('0.00'))

        order = Order.objects.create(
            **user_data,
            **address_data,
            subtotal=subtotal,
            shipping_cost=shipping_cost,
            discount=discount,
            notes=serializer.validated_data.get('notes', ''),
        )
        
        for product_info in products_info:
            OrderItem.objects.create(
                order=order,
                **product_info
            )
        
        for item_data in items_data:
            self._decrease_product_stock(
                item_data['product_id'],
                item_data['quantity'],
                request
            )
        
        OrderStatusHistory.objects.create(
            order=order,
            from_status=PENDING,
            to_status=PENDING,
            comment='Pedido criado',
            changed_by=user.id
        )
        
        return Response({
            'message': 'Pedido criado com sucesso!',
            'order': OrderDetailSerializer(order).data
        }, status=status.HTTP_201_CREATED)
    
    def retrieve(self, request, pk=None):
        order = self.get_object()
        serializer = self.get_serializer(order)
        return Response(serializer.data)

    def get_order_by_id(self, request, pk=None):
        try:
            order = self.get_queryset().get(pk=pk)
        except Order.DoesNotExist:
            return Response({'error': 'Pedido não encontrado.'}, status=status.HTTP_404_NOT_FOUND)

        user = request.user
        if not (hasattr(user, 'is_admin') and (user.is_admin or user.is_admin_master)):
            if order.user_id != getattr(user, 'id', None):
                return Response({'error': 'Acesso negado.'}, status=status.HTTP_403_FORBIDDEN)

        serializer = self.get_serializer(order)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        if not (hasattr(request.user, 'is_admin') and 
                (request.user.is_admin or request.user.is_admin_master)):
            return Response(
                {'error': 'Apenas administradores podem atualizar status.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        order = self.get_object()
        serializer = OrderUpdateStatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        new_status = serializer.validated_data['status']
        comment = serializer.validated_data.get('comment', '')
        tracking_code = serializer.validated_data.get('tracking_code', '')
        
        if order.status == CANCELLED:
            return Response(
                {'error': 'Pedido cancelado não pode ter status alterado.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if order.status == DELIVERED and new_status != DELIVERED:
            return Response(
                {'error': 'Pedido entregue não pode ter status alterado.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        old_status = order.status
        order.status = new_status
        
        if new_status == CONFIRMED and not order.confirmed_at:
            order.confirmed_at = timezone.now()
        elif new_status == SHIPPED and not order.shipped_at:
            order.shipped_at = timezone.now()
            if tracking_code:
                order.tracking_code = tracking_code
        elif new_status == DELIVERED and not order.delivered_at:
            order.delivered_at = timezone.now()
        
        order.save()
        
        OrderStatusHistory.objects.create(
            order=order,
            from_status=old_status,
            to_status=new_status,
            comment=comment,
            changed_by=request.user.id
        )
        
        return Response({
            'message': 'Status atualizado com sucesso!',
            'order': OrderDetailSerializer(order).data
        })
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        order = self.get_object()
        
        if not order.can_be_cancelled:
            return Response(
                {'error': 'Este pedido não pode ser cancelado.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = OrderCancelSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        old_status = order.status
        order.status = CANCELLED
        order.cancelled_at = timezone.now()
        order.save()
        
        for item in order.items.all():
            self._increase_product_stock(
                item.product_id,
                item.quantity,
                request
            )
        
        OrderStatusHistory.objects.create(
            order=order,
            from_status=old_status,
            to_status=CANCELLED,
            comment=serializer.validated_data['reason'],
            changed_by=request.user.id
        )
        
        return Response({
            'message': 'Pedido cancelado com sucesso!',
            'order': OrderDetailSerializer(order).data
        })
    
    @action(detail=False, methods=['get'])
    def my_orders(self, request):
        queryset = self.get_queryset().filter(user_id=request.user.id)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        if not (hasattr(request.user, 'is_admin') and 
                (request.user.is_admin or request.user.is_admin_master)):
            return Response(
                {'error': 'Apenas administradores podem ver estatísticas.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        queryset = Order.objects.all()
        
        stats = {
            'total_orders': queryset.count(),
            'pending': queryset.filter(status=PENDING).count(),
            'confirmed': queryset.filter(status=CONFIRMED).count(),
            'processing': queryset.filter(status=PROCESSING).count(),
            'shipped': queryset.filter(status=SHIPPED).count(),
            'delivered': queryset.filter(status=DELIVERED).count(),
            'cancelled': queryset.filter(status=CANCELLED).count(),
            'total_revenue': queryset.filter(
                status__in=[CONFIRMED, PROCESSING, SHIPPED, DELIVERED]
            ).aggregate(Sum('total'))['total__sum'] or Decimal('0.00'),
        }
        
        return Response(stats)
    
    def _get_product(self, product_id, request):
        try:
            products_url = os.getenv('PRODUCTS_SERVICE_URL', 'http://gestao-produtos-service:8002')
            token = request.headers.get('Authorization', '').replace('Bearer ', '')
            
            response = requests.get(
                f'{products_url}/api/v1/produtos/produto/{product_id}/',
                timeout=5
            )
            
            if response.status_code == 200:
                return response.json()
                
            return None
        except Exception as e:
            return None
    
    def _get_address(self, user_id, address_id, request):
        try:
            users_url = os.getenv('USERS_SERVICE_URL', 'http://gestao-usuarios-service:8001')
            token = request.headers.get('Authorization', '').replace('Bearer ', '')
            
            response = requests.get(
                f'{users_url}/api/v1/users/addresses/{address_id}/',
                headers={'Authorization': f'Bearer {token}'},
                timeout=5
            )
            
            if response.status_code == 200:
                addr = response.json()
                return {
                    'shipping_street': addr['street'],
                    'shipping_number': addr['number'],
                    'shipping_complement': addr.get('complement', ''),
                    'shipping_neighborhood': addr['neighborhood'],
                    'shipping_city': addr['city'],
                    'shipping_state': addr['state'],
                    'shipping_zip_code': addr['zip_code'],
                }
            return None
        except:
            return None
    
    def _decrease_product_stock(self, product_id, quantity, request):
        try:
            products_url = os.getenv('PRODUCTS_SERVICE_URL', 'http://gestao-produtos-service:8002')
            headers = {}
            for h in [
                'X-Forwarded-From-Gateway', 'X-User-ID', 'X-User-Email',
                'X-User-Nome', 'X-User-Is-Admin', 'X-User-Is-Staff',
                'X-User-CPF', 'X-User-Role', 'Authorization'
            ]:
                val = request.headers.get(h)
                if val:
                    headers[h] = val

            requests.post(
                f'{products_url}/api/v1/produtos/{product_id}/update-stock/',
                headers=headers if headers else None,
                json={'quantity': quantity, 'operation': 'remove'},
                timeout=5
            )
        except:
            pass

    def _increase_product_stock(self, product_id, quantity, request):
        try:
            products_url = os.getenv('PRODUCTS_SERVICE_URL', 'http://gestao-produtos-service:8002')
            headers = {}
            for h in [
                'X-Forwarded-From-Gateway', 'X-User-ID', 'X-User-Email',
                'X-User-Nome', 'X-User-Is-Admin', 'X-User-Is-Staff',
                'X-User-CPF', 'X-User-Role', 'Authorization'
            ]:
                val = request.headers.get(h)
                if val:
                    headers[h] = val

            requests.post(
                f'{products_url}/api/v1/produtos/{product_id}/update-stock/',
                headers=headers if headers else None,
                json={'quantity': quantity, 'operation': 'add'},
                timeout=5
            )
        except:
            pass
