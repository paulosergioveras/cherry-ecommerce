from django.contrib import admin
from django.utils.html import format_html
from .models import Notification, NotificationTemplate, NotificationPreference


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = (
        'id_display',
        'user_email',
        'notification_type_display',
        'category_display',
        'status_display',
        'title',
        'created_at',
    )
    list_filter = (
        'notification_type',
        'category',
        'status',
        'created_at',
    )
    search_fields = (
        'user_email',
        'title',
        'message',
    )
    readonly_fields = (
        'id',
        'user_id',
        'is_sent',
        'is_read',
        'is_failed',
        'can_retry',
        'created_at',
        'sent_at',
        'read_at',
    )
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Destinatário', {
            'fields': (
                'user_id',
                'user_email',
                'user_phone'
            )
        }),
        ('Tipo e Categoria', {
            'fields': (
                'notification_type',
                'category'
            )
        }),
        ('Conteúdo', {
            'fields': (
                'title',
                'message',
                'html_content',
                'data',
                'action_url'
            )
        }),
        ('Status', {
            'fields': (
                'status',
                'attempts',
                'error_message',
                'is_sent',
                'is_read',
                'is_failed',
                'can_retry'
            )
        }),
        ('Timestamps', {
            'fields': (
                'created_at',
                'sent_at',
                'read_at'
            ),
            'classes': ('collapse',)
        }),
    )
    
    def id_display(self, obj):
        return str(obj.id)[:8]
    id_display.short_description = 'ID'
    
    def notification_type_display(self, obj):
        icons = {
            'email': '📧',
            'sms': '💬',
            'push': '📱',
            'in_app': '🔔',
        }
        
        icon = icons.get(obj.notification_type, '📮')
        
        return format_html(
            '{} {}',
            icon,
            obj.get_notification_type_display()
        )
    notification_type_display.short_description = 'Tipo'
    
    def category_display(self, obj):
        colors = {
            'account': 'blue',
            'order': 'green',
            'payment': 'purple',
            'promotion': 'orange',
            'system': 'gray',
        }
        
        color = colors.get(obj.category, 'black')
        
        return format_html(
            '<span style="color: {};">{}</span>',
            color,
            obj.get_category_display()
        )
    category_display.short_description = 'Categoria'
    
    def status_display(self, obj):
        colors = {
            'pending': 'orange',
            'sending': 'blue',
            'sent': 'green',
            'failed': 'red',
            'read': 'teal',
        }
        
        color = colors.get(obj.status, 'gray')
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_display.short_description = 'Status'


@admin.register(NotificationTemplate)
class NotificationTemplateAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'notification_type_display',
        'category_display',
        'is_active',
        'created_at',
    )
    list_filter = (
        'notification_type',
        'category',
        'is_active',
        'created_at',
    )
    search_fields = (
        'name',
        'subject',
        'body',
    )
    readonly_fields = (
        'id',
        'created_at',
        'updated_at',
    )
    ordering = ('name',)
    
    fieldsets = (
        ('Identificação', {
            'fields': (
                'id',
                'name',
                'is_active'
            )
        }),
        ('Tipo e Categoria', {
            'fields': (
                'notification_type',
                'category'
            )
        }),
        ('Conteúdo', {
            'fields': (
                'subject',
                'body',
                'html_body'
            )
        }),
        ('Timestamps', {
            'fields': (
                'created_at',
                'updated_at'
            ),
            'classes': ('collapse',)
        }),
    )
    
    def notification_type_display(self, obj):
        icons = {
            'email': '📧',
            'sms': '💬',
            'push': '📱',
            'in_app': '🔔',
        }
        
        icon = icons.get(obj.notification_type, '📮')
        
        return format_html(
            '{} {}',
            icon,
            obj.get_notification_type_display()
        )
    notification_type_display.short_description = 'Tipo'
    
    def category_display(self, obj):
        return obj.get_category_display()
    category_display.short_description = 'Categoria'


@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(admin.ModelAdmin):
    list_display = (
        'user_id',
        'email_notifications',
        'sms_notifications',
        'push_notifications',
        'in_app_all',
        'created_at',
    )
    list_filter = (
        'email_order',
        'sms_order',
        'push_order',
        'in_app_all',
        'created_at',
    )
    search_fields = ('user_id',)
    readonly_fields = (
        'id',
        'user_id',
        'created_at',
        'updated_at',
    )
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Usuário', {
            'fields': (
                'id',
                'user_id'
            )
        }),
        ('Preferências de Email', {
            'fields': (
                'email_account',
                'email_order',
                'email_payment',
                'email_promotion'
            )
        }),
        ('Preferências de SMS', {
            'fields': (
                'sms_order',
                'sms_payment'
            )
        }),
        ('Preferências de Push', {
            'fields': (
                'push_order',
                'push_payment',
                'push_promotion'
            )
        }),
        ('Notificações no App', {
            'fields': ('in_app_all',)
        }),
        ('Timestamps', {
            'fields': (
                'created_at',
                'updated_at'
            ),
            'classes': ('collapse',)
        }),
    )
    
    def email_notifications(self, obj):
        count = sum([
            obj.email_account,
            obj.email_order,
            obj.email_payment,
            obj.email_promotion
        ])
        return f"{count}/4 ativadas"
    email_notifications.short_description = 'Email'
    
    def sms_notifications(self, obj):
        count = sum([
            obj.sms_order,
            obj.sms_payment
        ])
        return f"{count}/2 ativadas"
    sms_notifications.short_description = 'SMS'
    
    def push_notifications(self, obj):
        count = sum([
            obj.push_order,
            obj.push_payment,
            obj.push_promotion
        ])
        return f"{count}/3 ativadas"
    push_notifications.short_description = 'Push'
