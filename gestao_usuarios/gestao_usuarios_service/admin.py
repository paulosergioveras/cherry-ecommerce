from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User, Address


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Configuração do admin para o modelo User"""
    
    list_display = ('email', 'name', 'role', 'is_active', 'is_staff', 'created_at')
    list_filter = ('role', 'is_active', 'is_staff', 'is_superuser', 'created_at')
    search_fields = ('email', 'name', 'cpf', 'phone')
    ordering = ('-created_at',)
    
    fieldsets = (
        (None, {
            'fields': ('email', 'password')
        }),
        (_('Informações Pessoais'), {
            'fields': ('name', 'cpf', 'phone')
        }),
        (_('Tipo de Usuário'), {
            'fields': ('role',)
        }),
        (_('Permissões'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        (_('Datas Importantes'), {
            'fields': ('last_login', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'name', 'password1', 'password2', 'role'),
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at', 'last_login')
    
    def save_model(self, request, obj, form, change):
        """
        Sobrescreve o método save_model para garantir que:
        - Apenas admin master pode criar novos admins
        - Senhas sejam criptografadas corretamente
        """
        if not change:  # Se está criando um novo usuário
            if obj.role in ['admin', 'admin_master']:
                if not request.user.is_admin_master:
                    raise PermissionError('Apenas administradores master podem criar novos administradores.')
        
        super().save_model(request, obj, form, change)
    
    def get_queryset(self, request):
        """
        Filtra os usuários visíveis no admin baseado no tipo de usuário
        - Admin master vê todos
        - Admin vê apenas usuários e outros admins (não admin master)
        """
        qs = super().get_queryset(request)
        
        if request.user.is_admin_master:
            return qs
        elif request.user.is_admin:
            # Admin comum não vê admin master
            return qs.exclude(role='admin_master')
        
        return qs.none()  # Usuário comum não vê nada


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):    
    list_display = ('get_user_email', 'street', 'city', 'state', 'is_default', 'created_at')
    list_filter = ('state', 'city', 'is_default', 'created_at')
    search_fields = ('user__email', 'user__name', 'street', 'city', 'zip_code')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        (_('Usuário'), {
            'fields': ('user',)
        }),
        (_('Endereço'), {
            'fields': (
                'street', 'number', 'complement', 'neighborhood',
                'city', 'state', 'zip_code'
            )
        }),
        (_('Configurações'), {
            'fields': ('is_default',)
        }),
        (_('Datas'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_user_email(self, obj):
        return obj.user.email
    get_user_email.short_description = 'Email do Usuário'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        
        if request.user.is_admin or request.user.is_admin_master:
            return qs
        
        return qs.filter(user=request.user)
    
    def save_model(self, request, obj, form, change):
        if not (request.user.is_admin or request.user.is_admin_master):
            obj.user = request.user
        
        super().save_model(request, obj, form, change)
