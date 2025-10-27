from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.exceptions import ValidationError
import time
import re

# Simplified role model: use boolean flags instead of role string
CUSTOMER = 'customer'
ADMIN = 'admin'
ADMIN_MASTER = 'admin_master'

class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('O email é obrigatório')
        # CPF agora é obrigatório para todos os usuários
        cpf = extra_fields.get('cpf')
        if not cpf:
            raise ValueError('O CPF é obrigatório')
        
        email = self.normalize_email(email)
        extra_fields.setdefault('username', email)  # Username será o email
        # Garantir flags booleans padrão
        extra_fields.setdefault('is_admin', False)
        extra_fields.setdefault('is_admin_master', False)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_admin(self, email, cpf, password=None, **extra_fields):
        if not email:
            raise ValueError('O email é obrigatório')
        if not cpf:
            raise ValueError('O CPF é obrigatório para administradores')
        
        email = self.normalize_email(email)
        extra_fields.setdefault('username', email)
        # Marca como administrador simples
        extra_fields['is_admin'] = True
        extra_fields['is_staff'] = True
        user = self.model(email=email, cpf=cpf, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        # Marca como admin master
        extra_fields['is_admin_master'] = True
        extra_fields['is_admin'] = True
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser precisa ter is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser precisa ter is_superuser=True.')

        # generate a unique cpf if none provided to avoid UNIQUE conflicts
        cpf = extra_fields.get('cpf')
        if not cpf:
            # use time ns to generate a numeric 11-digit string
            cpf = str(time.time_ns())[-11:]
        return self.create_admin(email, cpf=cpf, password=password, **extra_fields)

class User(AbstractUser):
    email = models.EmailField(max_length=255, unique=True, db_index=True)
    name = models.CharField(max_length=255, blank=False)
    cpf = models.CharField(
        max_length=11,
        unique=True,
        null=False,
        blank=False,
        help_text="CPF obrigatório para todos os usuários"
    )
    phone = models.CharField(max_length=15, null=True, blank=True)
    # Simplified role flags
    is_admin = models.BooleanField(default=False)
    is_admin_master = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name']
    
    objects = UserManager()
    
    def __str__(self):
        return f"{self.name} ({self.email})"
    
    class Meta:
        db_table = 'users'
        verbose_name = 'Usuário'
        verbose_name_plural = 'Usuários'
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['is_admin']),
            models.Index(fields=['is_admin_master']),
        ]
    
    def clean(self):
        """
        Validações personalizadas
        """
        super().clean()
        
        # CPF obrigatório para todos os usuários
        if not self.cpf:
            raise ValidationError({'cpf': 'CPF é obrigatório'})
        if not self._validate_cpf(self.cpf):
            raise ValidationError({'cpf': 'CPF inválido'})
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
    
    @staticmethod
    def _validate_cpf(cpf):
        """
        Valida formato básico do CPF (11 dígitos numéricos)
        """
        if not cpf:
            return False
        cpf = re.sub(r'\D', '', cpf)
        return len(cpf) == 11 and cpf.isdigit()
    
    @property
    def is_customer(self):
        return not (self.is_admin or self.is_admin_master)
    
    
    def can_create_admin(self):
        """
        RN03: Apenas ADM master pode criar outros administradores
        """
        return self.is_admin_master


class Address(models.Model):
    """
    Endereços de entrega dos clientes
    Um cliente pode ter múltiplos endereços
    """
    
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='addresses'
    )
    
    street = models.CharField(max_length=255, verbose_name="Rua")
    number = models.CharField(max_length=20, verbose_name="Número")
    complement = models.CharField(max_length=100, null=True, blank=True, verbose_name="Complemento")
    neighborhood = models.CharField(max_length=100, verbose_name="Bairro")
    city = models.CharField(max_length=100, verbose_name="Cidade")
    state = models.CharField(max_length=2, verbose_name="Estado")
    zip_code = models.CharField(max_length=8, verbose_name="CEP")
    is_default = models.BooleanField(default=False, verbose_name="Endereço padrão")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'addresses'
        verbose_name = 'Endereço'
        verbose_name_plural = 'Endereços'
        ordering = ['-is_default', '-created_at']
    
    def __str__(self):
        return f"{self.street}, {self.number} - {self.city}/{self.state}"
    
    def save(self, *args, **kwargs):
        # Se este endereço é marcado como padrão, desmarca os outros
        if self.is_default:
            Address.objects.filter(user=self.user, is_default=True).update(is_default=False)
        super().save(*args, **kwargs)
