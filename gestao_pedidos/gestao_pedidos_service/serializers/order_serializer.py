from rest_framework import serializers
from decimal import Decimal
import requests
import os

from ..models import Order, OrderItem, OrderStatusHistory




class OrderItemSerializer(serializers.ModelSerializer):

    class Meta:
        model = OrderItem
        fields = '__all__'
        read_only_fields = ('id', 'subtotal')

class OrderItemCreateSerializer(serializers.Serializer):
    product_id = serializers.IntegerField(required=True)
    quantity = serializers.IntegerField(required=True, min_value=1)
    
    def validate_quantity(self, value):
        if value < 1:
            raise serializers.ValidationError('Quantidade deve ser maior que zero.')
        return value

class OrderStatusHistorySerializer(serializers.ModelSerializer):
    from_status_display = serializers.CharField(source='get_from_status_display', read_only=True)
    to_status_display = serializers.CharField(source='get_to_status_display', read_only=True)
    
    class Meta:
        model = OrderStatusHistory
        fields = '__all__'
        read_only_fields = ('id', 'created_at')

class OrderListSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display',read_only=True)
    order_number = serializers.CharField(read_only=True)
    items_count = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Order
        fields = (
            'id',
            'order_number',
            'user_name',
            'status',
            'status_display',
            'total',
            'items_count',
            'created_at',
        )
        read_only_fields = ('id', 'order_number', 'created_at')

class OrderDetailSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    order_number = serializers.CharField(read_only=True)
    items = OrderItemSerializer(many=True, read_only=True)
    items_count = serializers.IntegerField(read_only=True)
    can_be_cancelled = serializers.BooleanField(read_only=True)
    is_completed = serializers.BooleanField(read_only=True)
    is_cancelled = serializers.BooleanField(read_only=True)
    status_history = OrderStatusHistorySerializer(many=True, read_only=True)
    
    class Meta:
        model = Order
        fields = '__all__'
        read_only_fields = (
            'id',
            'order_number',
            'subtotal',
            'total',
            'created_at',
            'updated_at',
            'confirmed_at',
            'shipped_at',
            'delivered_at',
            'cancelled_at',
        )

class OrderCreateSerializer(serializers.Serializer):
    items = OrderItemCreateSerializer(many=True, required=True)

    shipping_cost = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        min_value=Decimal('0.00')
    )

    discount = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        min_value=Decimal('0.00')
    )
    
    address_id = serializers.IntegerField(required=False, allow_null=True)
    shipping_street = serializers.CharField(max_length=255, required=False)
    shipping_number = serializers.CharField(max_length=20, required=False)
    shipping_complement = serializers.CharField(max_length=100, required=False, allow_blank=True)
    shipping_neighborhood = serializers.CharField(max_length=100, required=False)
    shipping_city = serializers.CharField(max_length=100, required=False)
    shipping_state = serializers.CharField(max_length=2, required=False)
    shipping_zip_code = serializers.CharField(max_length=8, required=False)
    notes = serializers.CharField(required=False, allow_blank=True)
    
    def validate_items(self, value):
        if not value:
            raise serializers.ValidationError('O pedido deve ter pelo menos um item.')
        return value
    
    def validate(self, attrs):
        if not attrs.get('address_id'):
            required_fields = [
                'shipping_street',
                'shipping_number',
                'shipping_neighborhood',
                'shipping_city',
                'shipping_state',
                'shipping_zip_code'
            ]
            
            for field in required_fields:
                if not attrs.get(field):
                    raise serializers.ValidationError({
                        field: 'Este campo é obrigatório quando não fornece address_id.'
                    })
        
        return attrs

class OrderUpdateStatusSerializer(serializers.Serializer):
    status = serializers.ChoiceField(
        choices=['confirmed', 'processing', 'shipped', 'delivered', 'cancelled'],
        required=True
    )

    comment = serializers.CharField(required=False,allow_blank=True)
    tracking_code = serializers.CharField(required=False, allow_blank=True)

class OrderCancelSerializer(serializers.Serializer):
    reason = serializers.CharField(required=True)
