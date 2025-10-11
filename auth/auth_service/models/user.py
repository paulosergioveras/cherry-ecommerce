from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone
import uuid




class UserManager(BaseUserManager):
    """Manager customizado para o modelo User"""
    
    def create_user(self, email, password=None, **extra_fields):
        """Cria e retorna um usuário comum"""
        if not email:
            raise ValueError('O email é obrigatório')
        
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        """Cria e retorna um superusuário (admin)"""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_admin', True)
        extra_fields.setdefault('user_type', 'ADMIN')
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser precisa ter is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser precisa ter is_superuser=True.')
        
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """Modelo customizado de usuário"""
    
    USER_TYPE_CHOICES = (
        ('CUSTOMER', 'Cliente'),
        ('ADMIN', 'Administrador'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField('Email', unique=True, max_length=255)
    name = models.CharField('Nome', max_length=255)
    cpf = models.CharField('CPF', max_length=11, unique=True, null=True, blank=True)
    user_type = models.CharField('Tipo de Usuário', max_length=10, choices=USER_TYPE_CHOICES, default='CUSTOMER')
    
    is_active = models.BooleanField('Ativo', default=True)
    is_staff = models.BooleanField('Staff', default=False)
    is_admin = models.BooleanField('Admin', default=False)
    
    date_joined = models.DateTimeField('Data de Cadastro', default=timezone.now)
    last_login = models.DateTimeField('Último Login', null=True, blank=True)
    
    objects = UserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name']
    
    class Meta:
        verbose_name = 'Usuário'
        verbose_name_plural = 'Usuários'
        ordering = ['-date_joined']
    
    def __str__(self):
        return self.email
    
    def get_full_name(self):
        return self.name
    
    def get_short_name(self):
        return self.name.split()[0] if self.name else self.email


class UserSession(models.Model):
    """Modelo para rastrear sessões de usuários"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sessions')
    refresh_token = models.TextField('Refresh Token')
    ip_address = models.GenericIPAddressField('IP Address', null=True, blank=True)
    user_agent = models.TextField('User Agent', null=True, blank=True)
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    expires_at = models.DateTimeField('Expira em')
    is_active = models.BooleanField('Ativo', default=True)
    
    class Meta:
        verbose_name = 'Sessão de Usuário'
        verbose_name_plural = 'Sessões de Usuários'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.email} - {self.created_at}"
