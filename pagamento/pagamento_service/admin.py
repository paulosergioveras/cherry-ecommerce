from django.contrib import admin
from django.utils.html import format_html
from .models import Payment, PaymentStatusHistory, Refund




class PaymentStatusHistoryInline(admin.TabularInline):
    model = PaymentStatusHistory
    extra = 0
    fields = (
        'from_status',
        'to_status',
        'comment',
        'changed_by',
        'created_at'
    )
    readonly_fields = ('created_at',)
    can_delete = False

class RefundInline(admin.TabularInline):
    model = Refund
    extra = 0
    fields = (
        'amount',
        'reason',
        'status',
        'requested_by',
        'created_at',
        'completed_at'
    )
    readonly_fields = ('created_at', 'completed_at')
    can_delete = False

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        'payment_number_display',
        'user_name',
        'payment_method_display',
        'status_display',
        'amount_display',
        'created_at',
    )
    list_filter = (
        'status',
        'payment_method',
        'created_at',
        'approved_at',
    )
    search_fields = (
        'id',
        'order_id',
        'user_name',
        'user_email',
        'gateway_transaction_id'
    )
    readonly_fields = (
        'id',
        'payment_number',
        'order_id',
        'user_id',
        'is_approved',
        'is_pending',
        'can_be_refunded',
        'is_card_payment',
        'created_at',
        'updated_at',
        'processed_at',
        'approved_at',
        'refunded_at',
    )
    ordering = ('-created_at',)
    inlines = [PaymentStatusHistoryInline, RefundInline]
    
    fieldsets = (
        ('Informações do Pagamento', {
            'fields': (
                'id',
                'payment_number',
                'order_id',
                'payment_method',
                'status',
                'amount'
            )
        }),
        ('Cliente', {
            'fields': (
                'user_id',
                'user_name',
                'user_email'
            )
        }),
        ('Dados do Cartão', {
            'fields': (
                'card_holder_name',
                'card_number_last4',
                'card_brand',
                'installments'
            ),
            'classes': ('collapse',)
        }),
        ('Dados do PIX', {
            'fields': (
                'pix_key',
                'pix_qr_code',
                'pix_code'
            ),
            'classes': ('collapse',)
        }),
        ('Dados do Boleto', {
            'fields': (
                'boleto_barcode',
                'boleto_url',
                'boleto_due_date'
            ),
            'classes': ('collapse',)
        }),
        ('Gateway', {
            'fields': (
                'gateway_transaction_id',
                'gateway_response'
            ),
            'classes': ('collapse',)
        }),
        ('Observações', {
            'fields': (
                'notes',
                'decline_reason'
            ),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': (
                'is_approved',
                'is_pending',
                'can_be_refunded',
                'is_card_payment'
            )
        }),
        ('Datas', {
            'fields': (
                'created_at',
                'updated_at',
                'processed_at',
                'approved_at',
                'refunded_at'
            ),
            'classes': ('collapse',)
        }),
    )
    
    def payment_number_display(self, obj):
        return f"#{obj.payment_number}"
    payment_number_display.short_description = 'Nº Pagamento'
    
    def payment_method_display(self, obj):
        icons = {
            'credit_card': '💳',
            'debit_card': '💳',
            'pix': '📱',
            'boleto': '📄',
        }
        
        icon = icons.get(obj.payment_method, '💰')
        
        return format_html(
            '{} {}',
            icon,
            obj.get_payment_method_display()
        )
    payment_method_display.short_description = 'Método'
    
    def status_display(self, obj):
        """Exibe status com cores"""
        colors = {
            'pending': 'orange',
            'processing': 'blue',
            'approved': 'green',
            'declined': 'red',
            'refunded': 'purple',
            'cancelled': 'gray',
        }
        
        color = colors.get(obj.status, 'gray')
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_display.short_description = 'Status'
    
    def amount_display(self, obj):
        return format_html(
            '<strong>R$ {:.2f}</strong>',
            obj.amount
        )
    amount_display.short_description = 'Valor'
    
    def has_delete_permission(self, request, obj=None):
        return False

@admin.register(PaymentStatusHistory)
class PaymentStatusHistoryAdmin(admin.ModelAdmin): 
    list_display = (
        'payment_number_display',
        'from_status_display',
        'to_status_display',
        'changed_by',
        'created_at',
    )
    list_filter = (
        'from_status',
        'to_status',
        'created_at'
    )
    search_fields = (
        'payment__id',
        'comment'
    )
    readonly_fields = (
        'payment',
        'from_status',
        'to_status',
        'comment',
        'changed_by',
        'created_at'
    )
    ordering = ('-created_at',)
    
    def payment_number_display(self, obj):
        return f"#{obj.payment.payment_number}"
    payment_number_display.short_description = 'Nº Pagamento'
    
    def from_status_display(self, obj):
        return format_html(
            '<span style="color: gray;">{}</span>',
            obj.get_from_status_display()
        )
    from_status_display.short_description = 'De'
    
    def to_status_display(self, obj):
        colors = {
            'pending': 'orange',
            'processing': 'blue',
            'approved': 'green',
            'declined': 'red',
            'refunded': 'purple',
            'cancelled': 'gray',
        }
        
        color = colors.get(obj.to_status, 'gray')
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_to_status_display()
        )
    to_status_display.short_description = 'Para'
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Refund)
class RefundAdmin(admin.ModelAdmin):
    list_display = (
        'refund_id_display',
        'payment_number_display',
        'amount_display',
        'status_display',
        'requested_by',
        'created_at',
    )
    list_filter = (
        'status',
        'created_at',
        'completed_at'
    )
    search_fields = (
        'id',
        'payment__id',
        'reason'
    )
    readonly_fields = (
        'id',
        'payment',
        'amount',
        'reason',
        'requested_by',
        'gateway_refund_id',
        'created_at',
        'completed_at'
    )
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Informações do Reembolso', {
            'fields': (
                'id',
                'payment',
                'amount',
                'reason',
                'status'
            )
        }),
        ('Gateway', {
            'fields': ('gateway_refund_id',)
        }),
        ('Rastreamento', {
            'fields': (
                'requested_by',
                'created_at',
                'completed_at'
            )
        }),
    )
    
    def refund_id_display(self, obj):
        return f"#{str(obj.id)[:8]}"
    refund_id_display.short_description = 'ID'
    
    def payment_number_display(self, obj):
        return f"#{obj.payment.payment_number}"
    payment_number_display.short_description = 'Pagamento'
    
    def amount_display(self, obj):
        return format_html(
            '<strong>R$ {:.2f}</strong>',
            obj.amount
        )
    amount_display.short_description = 'Valor'
    
    def status_display(self, obj):
        colors = {
            'pending': 'orange',
            'processing': 'blue',
            'completed': 'green',
            'failed': 'red',
        }
        
        color = colors.get(obj.status, 'gray')
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_display.short_description = 'Status'
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False
