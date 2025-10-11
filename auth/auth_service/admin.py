from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import UserChangeForm, UserCreationForm
from .models import User, UserSession




class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('email', 'name', 'user_type')

class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = User
        fields = '__all__'

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    form = CustomUserChangeForm
    add_form = CustomUserCreationForm
    
    list_display = ('email', 'name', 'user_type', 'is_active', 'is_admin', 'date_joined')
    list_filter = ('user_type', 'is_active', 'is_admin', 'date_joined')
    search_fields = ('email', 'name', 'cpf')
    ordering = ('-date_joined',)
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Informações Pessoais', {'fields': ('name', 'cpf')}),
        ('Permissões', {
            'fields': ('user_type', 'is_active', 'is_staff', 'is_admin', 'is_superuser', 'groups', 'user_permissions'),
        }),
        ('Datas Importantes', {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'name', 'user_type', 'password1', 'password2'),
        }),
    )
    
    readonly_fields = ('date_joined', 'last_login')
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs


@admin.register(UserSession)
class UserSessionAdmin(admin.ModelAdmin):
    list_display = ('user', 'ip_address', 'created_at', 'expires_at', 'is_active')
    list_filter = ('is_active', 'created_at', 'expires_at')
    search_fields = ('user__email', 'ip_address')
    ordering = ('-created_at',)
    readonly_fields = ('user', 'refresh_token', 'ip_address', 'user_agent', 'created_at', 'expires_at')
    
    fieldsets = (
        ('Informações da Sessão', {
            'fields': ('user', 'is_active')
        }),
        ('Detalhes Técnicos', {
            'fields': ('refresh_token', 'ip_address', 'user_agent')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'expires_at')
        }),
    )
    
    def has_add_permission(self, request):
        return False
