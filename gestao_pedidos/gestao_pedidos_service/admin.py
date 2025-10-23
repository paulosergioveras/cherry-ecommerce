from django.contrib import admin
from django.utils.html import format_html
from .models import Order, OrderItem, OrderStatusHistory




class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    fields = (
        'product_name',
        'product_sku',
        'quantity',
        'unit_price',
        'subtotal'
    )
    readonly_fields = ('subtotal',)
    can_delete = False


class OrderStatusHistoryInline(admin.TabularInline):
    model = OrderStatusHistory
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


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        'order_number_display',
        'user_name',
        'status_display',
        'total_display',
        'items_count',
        'created_at',
    )
    list_filter = (
        'status',
        'created_at',
        'confirmed_at',
        'shipped_at',
        'delivered_at',
    )
    search_fields = (
        'id',
        'user_name',
        'user_email',
        'tracking_code'
    )
    readonly_fields = (
        'id',
        'order_number',
        'user_id',
        'subtotal',
        'total',
        'items_count',
        'can_be_cancelled',
        'is_completed',
        'is_cancelled',
        'created_at',
        'updated_at',
        'confirmed_at',
        'shipped_at',
        'delivered_at',
        'cancelled_at',
    )
    ordering = ('-created_at',)
    inlines = [OrderItemInline, OrderStatusHistoryInline]
    
    fieldsets = (
        ('Informações do Pedido', {
            'fields': (
                'id',
                'order_number',
                'status',
                'tracking_code'
            )
        }),
        ('Cliente', {
            'fields': (
                'user_id',
                'user_name',
                'user_email',
                'user_phone'
            )
        }),
        ('Valores', {
            'fields': (
                'subtotal',
                'shipping_cost',
                'discount',
                'total'
            )
        }),
        ('Endereço de Entrega', {
            'fields': (
                'shipping_street',
                'shipping_number',
                'shipping_complement',
                'shipping_neighborhood',
                'shipping_city',
                'shipping_state',
                'shipping_zip_code'
            )
        }),
        ('Observações', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': (
                'can_be_cancelled',
                'is_completed',
                'is_cancelled',
                'items_count'
            )
        }),
        ('Datas', {
            'fields': (
                'created_at',
                'updated_at',
                'confirmed_at',
                'shipped_at',
                'delivered_at',
                'cancelled_at'
            ),
            'classes': ('collapse',)
        }),
    )
    
    def order_number_display(self, obj):
        return f"#{obj.order_number}"
    order_number_display.short_description = 'Nº Pedido'
    
    def status_display(self, obj):
        colors = {
            'pending': 'orange',
            'confirmed': 'blue',
            'processing': 'purple',
            'shipped': 'teal',
            'delivered': 'green',
            'cancelled': 'red',
        }
        
        color = colors.get(obj.status, 'gray')
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_display.short_description = 'Status'
    
    def total_display(self, obj):
        return format_html(
            '<strong>R$ {:.2f}</strong>',
            obj.total
        )
    total_display.short_description = 'Total'
    
    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = (
        'order_number_display',
        'product_name',
        'quantity',
        'unit_price_display',
        'subtotal_display',
    )
    list_filter = ('created_at',)
    search_fields = (
        'order__id',
        'product_name',
        'product_sku'
    )
    readonly_fields = (
        'order',
        'product_id',
        'product_name',
        'product_sku',
        'product_image',
        'quantity',
        'unit_price',
        'subtotal',
        'created_at'
    )
    ordering = ('-created_at',)
    
    def order_number_display(self, obj):
        return f"#{obj.order.order_number}"
    order_number_display.short_description = 'Nº Pedido'
    
    def unit_price_display(self, obj):
        return f"R$ {obj.unit_price:.2f}"
    unit_price_display.short_description = 'Preço Unit.'
    
    def subtotal_display(self, obj):
        return format_html(
            '<strong>R$ {:.2f}</strong>',
            obj.subtotal
        )
    subtotal_display.short_description = 'Subtotal'
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(OrderStatusHistory)
class OrderStatusHistoryAdmin(admin.ModelAdmin): 
    list_display = (
        'order_number_display',
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
        'order__id',
        'comment'
    )
    readonly_fields = (
        'order',
        'from_status',
        'to_status',
        'comment',
        'changed_by',
        'created_at'
    )
    ordering = ('-created_at',)
    
    def order_number_display(self, obj):
        return f"#{obj.order.order_number}"
    order_number_display.short_description = 'Nº Pedido'
    
    def from_status_display(self, obj):
        return format_html(
            '<span style="color: gray;">{}</span>',
            obj.get_from_status_display()
        )
    from_status_display.short_description = 'De'
    
    def to_status_display(self, obj):
        colors = {
            'pending': 'orange',
            'confirmed': 'blue',
            'processing': 'purple',
            'shipped': 'teal',
            'delivered': 'green',
            'cancelled': 'red',
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
