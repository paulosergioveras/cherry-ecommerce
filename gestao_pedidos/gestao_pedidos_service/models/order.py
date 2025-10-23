from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal
import uuid

PENDING = 'pending'
CONFIRMED = 'confirmed'
PROCESSING = 'processing'
SHIPPED = 'shipped'
DELIVERED = 'delivered'
CANCELLED = 'cancelled'

ORDER_STATUS_CHOICES = [
    (PENDING, 'Pendente'),
    (CONFIRMED, 'Confirmado'),
    (PROCESSING, 'Em Processamento'),
    (SHIPPED, 'Enviado'),
    (DELIVERED, 'Entregue'),
    (CANCELLED, 'Cancelado'),
]

class Order(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.IntegerField(verbose_name='ID do Usuário')
    user_name = models.CharField(max_length=255, verbose_name='Nome do Cliente')
    user_email = models.EmailField(verbose_name='Email do Cliente')
    user_phone = models.CharField(max_length=15, blank=True, verbose_name='Telefone do Cliente')
    
    status = models.CharField(
        max_length=20,
        choices=ORDER_STATUS_CHOICES,
        default=PENDING,
        verbose_name='Status'
    )
    
    subtotal = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name='Subtotal'
    )

    shipping_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name='Frete'
    )

    discount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name='Desconto'
    )

    total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name='Total'
    )
    
    shipping_street = models.CharField(max_length=255, verbose_name='Rua')
    shipping_number = models.CharField(max_length=20, verbose_name='Número')
    shipping_complement = models.CharField(max_length=100, blank=True, verbose_name='Complemento')
    shipping_neighborhood = models.CharField(max_length=100, verbose_name='Bairro')
    shipping_city = models.CharField(max_length=100, verbose_name='Cidade')
    shipping_state = models.CharField(max_length=2, verbose_name='Estado')
    shipping_zip_code = models.CharField(max_length=8, verbose_name='CEP')
    notes = models.TextField(blank=True, verbose_name='Observações')
    tracking_code = models.CharField(max_length=100, blank=True, verbose_name='Código de Rastreio')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Atualizado em')
    confirmed_at = models.DateTimeField(null=True, blank=True, verbose_name='Confirmado em')
    shipped_at = models.DateTimeField(null=True, blank=True, verbose_name='Enviado em')
    delivered_at = models.DateTimeField(null=True, blank=True, verbose_name='Entregue em')
    cancelled_at = models.DateTimeField(null=True, blank=True, verbose_name='Cancelado em')
    
    class Meta:
        db_table = 'orders'
        verbose_name = 'Pedido'
        verbose_name_plural = 'Pedidos'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user_id']),
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"Pedido #{str(self.id)[:8]} - {self.user_name}"
    
    def save(self, *args, **kwargs):
        self.total = self.subtotal + self.shipping_cost - self.discount
        super().save(*args, **kwargs)
    
    @property
    def order_number(self):
        return str(self.id)[:8].upper()
    
    @property
    def items_count(self):
        return sum(item.quantity for item in self.items.all())
    
    @property
    def can_be_cancelled(self):
        return self.status in [PENDING, CONFIRMED]
    
    @property
    def is_completed(self):
        return self.status == DELIVERED
    
    @property
    def is_cancelled(self):
        return self.status == CANCELLED

class OrderItem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items', verbose_name='Pedido')
    product_id = models.IntegerField(verbose_name='ID do Produto')
    product_name = models.CharField(max_length=200, verbose_name='Nome do Produto')
    product_sku = models.CharField(max_length=50, verbose_name='SKU')
    product_image = models.URLField(blank=True,verbose_name='Imagem do Produto')
    quantity = models.IntegerField(validators=[MinValueValidator(1)], verbose_name='Quantidade')

    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name='Preço Unitário'
    )

    subtotal = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name='Subtotal'
    )
    
    created_at = models.DateTimeField(auto_now_add=True,verbose_name='Criado em')
    
    class Meta:
        db_table = 'order_items'
        verbose_name = 'Item do Pedido'
        verbose_name_plural = 'Itens do Pedido'
        ordering = ['created_at']
    
    def __str__(self):
        return f"{self.product_name} x {self.quantity}"
    
    def save(self, *args, **kwargs):
        self.subtotal = self.unit_price * self.quantity
        super().save(*args, **kwargs)

class OrderStatusHistory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='status_history',
        verbose_name='Pedido'
    )
    
    from_status = models.CharField(
        max_length=20,
        choices=ORDER_STATUS_CHOICES,
        verbose_name='Status Anterior'
    )
    
    to_status = models.CharField(
        max_length=20,
        choices=ORDER_STATUS_CHOICES,
        verbose_name='Novo Status'
    )
    
    comment = models.TextField(blank=True, verbose_name='Comentário')
    changed_by = models.IntegerField(null=True, blank=True,verbose_name='Alterado por (User ID)')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Data da Mudança')
    
    class Meta:
        db_table = 'order_status_history'
        verbose_name = 'Histórico de Status'
        verbose_name_plural = 'Histórico de Status'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.from_status} → {self.to_status}"
