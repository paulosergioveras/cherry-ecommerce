from django.db import models
import uuid


EMAIL = 'email'
SMS = 'sms'
PUSH = 'push'
IN_APP = 'in_app'

NOTIFICATION_TYPE_CHOICES = [
    (EMAIL, 'Email'),
    (SMS, 'SMS'),
    (PUSH, 'Push Notification'),
    (IN_APP, 'Notificação no App'),
]

ACCOUNT = 'account'
ORDER = 'order'
PAYMENT = 'payment'
PROMOTION = 'promotion'
SYSTEM = 'system'

CATEGORY_CHOICES = [
    (ACCOUNT, 'Conta'),
    (ORDER, 'Pedido'),
    (PAYMENT, 'Pagamento'),
    (PROMOTION, 'Promoção'),
    (SYSTEM, 'Sistema'),
]

PENDING = 'pending'
SENDING = 'sending'
SENT = 'sent'
FAILED = 'failed'
READ = 'read'

STATUS_CHOICES = [
    (PENDING, 'Pendente'),
    (SENDING, 'Enviando'),
    (SENT, 'Enviado'),
    (FAILED, 'Falhou'),
    (READ, 'Lido'),
]




class Notification(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.IntegerField(verbose_name='ID do Usuário', db_index=True)
    user_email = models.EmailField(verbose_name='Email do Usuário')
    user_phone = models.CharField(max_length=15, blank=True, verbose_name='Telefone do Usuário')
    
    notification_type = models.CharField(
        max_length=20,
        choices=NOTIFICATION_TYPE_CHOICES,
        verbose_name='Tipo'
    )

    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        verbose_name='Categoria'
    )
    
    title = models.CharField(max_length=255, verbose_name='Título')
    message = models.TextField(verbose_name='Mensagem')

    html_content = models.TextField(
        blank=True,
        verbose_name='Conteúdo HTML',
        help_text='Para emails HTML'
    )
    
    data = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='Dados Adicionais',
        help_text='Dados extras como order_id, payment_id, etc.'
    )
    
    action_url = models.URLField(blank=True, verbose_name='URL de Ação')
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=PENDING,
        verbose_name='Status'
    )
    
    attempts = models.IntegerField(default=0, verbose_name='Tentativas de Envio')
    error_message = models.TextField(blank=True, verbose_name='Mensagem de Erro')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    sent_at = models.DateTimeField(null=True, blank=True, verbose_name='Enviado em')
    read_at = models.DateTimeField(null=True, blank=True, verbose_name='Lido em')
    
    class Meta:
        db_table = 'notifications'
        verbose_name = 'Notificação'
        verbose_name_plural = 'Notificações'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user_id']),
            models.Index(fields=['status']),
            models.Index(fields=['notification_type']),
            models.Index(fields=['category']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.get_notification_type_display()} - {self.title}"
    
    @property
    def is_sent(self):
        return self.status == SENT
    
    @property
    def is_read(self):
        return self.status == READ
    
    @property
    def is_failed(self):
        return self.status == FAILED
    
    @property
    def can_retry(self):
        return self.status == FAILED and self.attempts < 3


class NotificationTemplate(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name='Nome',
        help_text='Nome identificador do template'
    )
    
    notification_type = models.CharField(
        max_length=20,
        choices=NOTIFICATION_TYPE_CHOICES,
        verbose_name='Tipo'
    )
    
    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        verbose_name='Categoria'
    )
    
    subject = models.CharField(
        max_length=255,
        verbose_name='Assunto',
        help_text='Para emails. Suporta variáveis: {{var}}'
    )
    
    body = models.TextField(
        verbose_name='Corpo',
        help_text='Mensagem. Suporta variáveis: {{var}}'
    )
    
    html_body = models.TextField(
        blank=True,
        verbose_name='Corpo HTML',
        help_text='Para emails HTML. Suporta variáveis: {{var}}'
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name='Ativo'
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Criado em'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Atualizado em'
    )
    
    class Meta:
        db_table = 'notification_templates'
        verbose_name = 'Template de Notificação'
        verbose_name_plural = 'Templates de Notificação'
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.get_notification_type_display()})"
    
    def render(self, context):
        subject = self.subject
        body = self.body
        html_body = self.html_body
        
        for key, value in context.items():
            placeholder = f"{{{{{key}}}}}"
            subject = subject.replace(placeholder, str(value))
            body = body.replace(placeholder, str(value))
            if html_body:
                html_body = html_body.replace(placeholder, str(value))
        
        return {
            'subject': subject,
            'body': body,
            'html_body': html_body
        }

class NotificationPreference(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    
    user_id = models.IntegerField(
        unique=True,
        verbose_name='ID do Usuário',
        db_index=True
    )

    email_account = models.BooleanField(
        default=True,
        verbose_name='Email - Conta'
    )
    email_order = models.BooleanField(
        default=True,
        verbose_name='Email - Pedidos'
    )
    email_payment = models.BooleanField(
        default=True,
        verbose_name='Email - Pagamentos'
    )
    email_promotion = models.BooleanField(
        default=True,
        verbose_name='Email - Promoções'
    )
    
    sms_order = models.BooleanField(
        default=False,
        verbose_name='SMS - Pedidos'
    )
    sms_payment = models.BooleanField(
        default=False,
        verbose_name='SMS - Pagamentos'
    )
    
    push_order = models.BooleanField(
        default=True,
        verbose_name='Push - Pedidos'
    )
    push_payment = models.BooleanField(
        default=True,
        verbose_name='Push - Pagamentos'
    )
    push_promotion = models.BooleanField(
        default=True,
        verbose_name='Push - Promoções'
    )
    
    in_app_all = models.BooleanField(
        default=True,
        verbose_name='Notificações no App'
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Criado em'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Atualizado em'
    )
    
    class Meta:
        db_table = 'notification_preferences'
        verbose_name = 'Preferência de Notificação'
        verbose_name_plural = 'Preferências de Notificação'
    
    def __str__(self):
        return f"Preferências do usuário {self.user_id}"
    
    def can_receive(self, notification_type, category):
        field_name = f"{notification_type}_{category}"
        
        if not hasattr(self, field_name):
            return True
        
        return getattr(self, field_name, True)
