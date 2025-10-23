from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal
import uuid


CREDIT_CARD = 'credit_card'
DEBIT_CARD = 'debit_card'
PIX = 'pix'
BOLETO = 'boleto'

PAYMENT_METHOD_CHOICES = [
    (CREDIT_CARD, 'Cartão de Crédito'),
    (DEBIT_CARD, 'Cartão de Débito'),
    (PIX, 'PIX'),
    (BOLETO, 'Boleto Bancário'),
]

PENDING = 'pending'
PROCESSING = 'processing'
APPROVED = 'approved'
DECLINED = 'declined'
REFUNDED = 'refunded'
CANCELLED = 'cancelled'

PAYMENT_STATUS_CHOICES = [
    (PENDING, 'Pendente'),
    (PROCESSING, 'Processando'),
    (APPROVED, 'Aprovado'),
    (DECLINED, 'Recusado'),
    (REFUNDED, 'Reembolsado'),
    (CANCELLED, 'Cancelado'),
]




class Payment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order_id = models.UUIDField(verbose_name='ID do Pedido', db_index=True)
    user_id = models.IntegerField(verbose_name='ID do Usuário', db_index=True)
    user_name = models.CharField(max_length=255, verbose_name='Nome do Cliente')
    user_email = models.EmailField(verbose_name='Email do Cliente')
    
    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHOD_CHOICES,
        verbose_name='Método de Pagamento'
    )

    status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default=PENDING,
        verbose_name='Status'
    )
    
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name='Valor'
    )
    
    card_holder_name = models.CharField(max_length=255, blank=True, verbose_name='Nome no Cartão')
    card_number_last4 = models.CharField(max_length=4, blank=True, verbose_name='Últimos 4 dígitos')
    card_brand = models.CharField(max_length=50, blank=True, verbose_name='Bandeira')

    installments = models.IntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        verbose_name='Parcelas'
    )
    
    pix_key = models.CharField(max_length=255, blank=True, verbose_name='Chave PIX')
    pix_qr_code = models.TextField(blank=True, verbose_name='QR Code PIX')
    pix_code = models.TextField(blank=True, verbose_name='Código PIX Copia e Cola')
    boleto_barcode = models.CharField(max_length=100, blank=True, verbose_name='Código de Barras')
    boleto_url = models.URLField(blank=True, verbose_name='URL do Boleto')
    boleto_due_date = models.DateField(null=True, blank=True, verbose_name='Data de Vencimento')
    
    gateway_transaction_id = models.CharField(
        max_length=255,
        blank=True,
        verbose_name='ID da Transação no Gateway'
    )

    gateway_response = models.JSONField(default=dict, blank=True, verbose_name='Resposta do Gateway')
    notes = models.TextField(blank=True, verbose_name='Observações')
    decline_reason = models.TextField(blank=True, verbose_name='Motivo da Recusa')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Atualizado em')
    processed_at = models.DateTimeField(null=True, blank=True, verbose_name='Processado em')
    approved_at = models.DateTimeField(null=True, blank=True, verbose_name='Aprovado em')
    refunded_at = models.DateTimeField(null=True, blank=True, verbose_name='Reembolsado em')
    
    class Meta:
        db_table = 'payments'
        verbose_name = 'Pagamento'
        verbose_name_plural = 'Pagamentos'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['order_id']),
            models.Index(fields=['user_id']),
            models.Index(fields=['status']),
            models.Index(fields=['payment_method']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"Pagamento {str(self.id)[:8]} - {self.get_payment_method_display()}"
    
    @property
    def payment_number(self):
        return str(self.id)[:8].upper()
    
    @property
    def is_approved(self):
        return self.status == APPROVED
    
    @property
    def is_pending(self):
        return self.status == PENDING
    
    @property
    def can_be_refunded(self):
        return self.status == APPROVED
    
    @property
    def is_card_payment(self):
        return self.payment_method in [CREDIT_CARD, DEBIT_CARD]

class PaymentStatusHistory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    payment = models.ForeignKey(
        Payment,
        on_delete=models.CASCADE,
        related_name='status_history',
        verbose_name='Pagamento'
    )
    
    from_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        verbose_name='Status Anterior'
    )

    to_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        verbose_name='Novo Status'
    )
    
    comment = models.TextField(blank=True, verbose_name='Comentário')
    
    changed_by = models.IntegerField(null=True, blank=True, verbose_name='Alterado por (User ID)')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Data da Mudança')
    
    class Meta:
        db_table = 'payment_status_history'
        verbose_name = 'Histórico de Status do Pagamento'
        verbose_name_plural = 'Histórico de Status dos Pagamentos'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.from_status} → {self.to_status}"

class Refund(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    payment = models.ForeignKey(
        Payment,
        on_delete=models.CASCADE,
        related_name='refunds',
        verbose_name='Pagamento'
    )
    
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name='Valor do Reembolso'
    )
    
    reason = models.TextField(verbose_name='Motivo')
    
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pendente'),
            ('processing', 'Processando'),
            ('completed', 'Concluído'),
            ('failed', 'Falhou'),
        ],
        default='pending',
        verbose_name='Status'
    )
    
    gateway_refund_id = models.CharField(
        max_length=255,
        blank=True,
        verbose_name='ID do Reembolso no Gateway'
    )
    
    requested_by = models.IntegerField(verbose_name='Solicitado por (User ID)')
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Solicitado em')
    
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Concluído em'
    )
    
    class Meta:
        db_table = 'refunds'
        verbose_name = 'Reembolso'
        verbose_name_plural = 'Reembolsos'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Reembolso {str(self.id)[:8]} - R$ {self.amount}"
