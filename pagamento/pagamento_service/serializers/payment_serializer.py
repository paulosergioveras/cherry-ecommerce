from rest_framework import serializers
from decimal import Decimal
from datetime import datetime, timedelta

from ..models import Payment, PaymentStatusHistory, Refund




class PaymentStatusHistorySerializer(serializers.ModelSerializer):
    from_status_display = serializers.CharField(source='get_from_status_display', read_only=True)
    to_status_display = serializers.CharField(source='get_to_status_display', read_only=True)
    
    class Meta:
        model = PaymentStatusHistory
        fields = (
            'id',
            'from_status',
            'from_status_display',
            'to_status',
            'to_status_display',
            'comment',
            'changed_by',
            'created_at',
        )
        read_only_fields = ('id', 'created_at')

class RefundSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Refund
        fields = (
            'id',
            'payment',
            'amount',
            'reason',
            'status',
            'status_display',
            'requested_by',
            'created_at',
            'completed_at',
        )
        read_only_fields = ('id', 'created_at', 'completed_at')

class PaymentListSerializer(serializers.ModelSerializer):
    payment_method_display = serializers.CharField(source='get_payment_method_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    payment_number = serializers.CharField(read_only=True)
    
    class Meta:
        model = Payment
        fields = (
            'id',
            'payment_number',
            'order_id',
            'payment_method',
            'payment_method_display',
            'status',
            'status_display',
            'amount',
            'created_at',
        )
        read_only_fields = ('id', 'payment_number', 'created_at')

class PaymentDetailSerializer(serializers.ModelSerializer):
    payment_method_display = serializers.CharField(source='get_payment_method_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    payment_number = serializers.CharField(read_only=True)
    is_approved = serializers.BooleanField(read_only=True)
    is_pending = serializers.BooleanField(read_only=True)
    can_be_refunded = serializers.BooleanField(read_only=True)
    is_card_payment = serializers.BooleanField(read_only=True)
    status_history = PaymentStatusHistorySerializer(many=True, read_only=True)
    refunds = RefundSerializer(many=True, read_only=True)
    
    class Meta:
        model = Payment
        fields = '__all__'
        read_only_fields = (
            'id',
            'payment_number',
            'created_at',
            'updated_at',
            'processed_at',
            'approved_at',
            'refunded_at',
        )

class PaymentCreateSerializer(serializers.Serializer):
    order_id = serializers.UUIDField(required=True)

    payment_method = serializers.ChoiceField(
        choices=['credit_card', 'debit_card', 'pix', 'boleto'],
        required=True
    )
    
    card_holder_name = serializers.CharField(required=False, max_length=255)
    card_number = serializers.CharField(required=False, max_length=19)
    card_expiry = serializers.CharField(required=False, max_length=7)
    card_cvv = serializers.CharField(required=False, max_length=4)

    installments = serializers.IntegerField(
        required=False,
        default=1,
        min_value=1,
        max_value=12
    )
    
    pix_key = serializers.CharField(required=False,allow_blank=True)
    
    def validate(self, attrs):
        payment_method = attrs.get('payment_method')
        
        if payment_method in ['credit_card', 'debit_card']:
            required_fields = [
                'card_holder_name',
                'card_number',
                'card_expiry',
                'card_cvv'
            ]
            
            for field in required_fields:
                if not attrs.get(field):
                    raise serializers.ValidationError({
                        field: f'Este campo é obrigatório para pagamento com {payment_method}.'
                    })
            
            card_number = attrs['card_number'].replace(' ', '')
            if not card_number.isdigit() or len(card_number) < 13:
                raise serializers.ValidationError({
                    'card_number': 'Número de cartão inválido.'
                })
            
            if not attrs['card_cvv'].isdigit() or len(attrs['card_cvv']) not in [3, 4]:
                raise serializers.ValidationError({
                    'card_cvv': 'CVV inválido.'
                })
        
        return attrs

class PaymentUpdateStatusSerializer(serializers.Serializer):
    status = serializers.ChoiceField(
        choices=['processing', 'approved', 'declined', 'cancelled'],
        required=True
    )

    comment = serializers.CharField(required=False,allow_blank=True)
    decline_reason = serializers.CharField(required=False, allow_blank=True)

class RefundRequestSerializer(serializers.Serializer):
    amount = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False  # Se não fornecido, reembolsa valor total
    )

    reason = serializers.CharField(required=True)
    
    def validate_amount(self, value):
        if value and value <= 0:
            raise serializers.ValidationError(
                'O valor deve ser maior que zero.'
            )
        return value
