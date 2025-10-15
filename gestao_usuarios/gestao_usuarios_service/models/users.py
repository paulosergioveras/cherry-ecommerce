from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.exceptions import ValidationError
import re


class UserManager(BaseUserManager):
    """
    Manager customizado para criação de usuários do e-commerce Cherry
    """
    
    def create_user(self, email, password=None, **extra_fields):
        """
        Cria um usuário comum (cliente)
        """
        if not email:
            raise ValueError('O email é obrigatório')
        
        email = self.normalize_email(email)
        extra_fields.setdefault('username', email)  # Username será o email
        extra_fields.setdefault('role', User.CUSTOMER)
        
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_admin(self, email, cpf, password=None, **extra_fields):
        """
        Cria um administrador (apenas ADM master pode criar)
        """
        if not email:
            raise ValueError('O email é obrigatório')
        if not cpf:
            raise ValueError('O CPF é obrigatório para administradores')
        
        email = self.normalize_email(email)
        extra_fields.setdefault('username', email)
        extra_fields['role'] = User.ADMIN
        extra_fields['is_staff'] = True
        
        user = self.model(email=email, cpf=cpf, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        """
        Cria um ADM Master (superusuário)
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields['role'] = User.ADMIN_MASTER
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser precisa ter is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser precisa ter is_superuser=True.')
        
        return self.create_admin(email, cpf='00000000000', password=password, **extra_fields)


class User(AbstractUser):
    """
    Model de Usuário para o E-commerce Cherry
    Gerencia clientes e administradores
    """
    
    # Roles do sistema
    CUSTOMER = 'customer'
    ADMIN = 'admin'
    ADMIN_MASTER = 'admin_master'
    
    ROLE_CHOICES = [
        (CUSTOMER, 'Cliente'),
        (ADMIN, 'Administrador'),
        (ADMIN_MASTER, 'Administrador Master'),
    ]
    
    # Campos básicos
    email = models.EmailField(max_length=255, unique=True, db_index=True)
    name = models.CharField(max_length=255, blank=False)
    cpf = models.CharField(
        max_length=11, 
        unique=True, 
        null=True, 
        blank=True,
        help_text="CPF obrigatório apenas para administradores"
    )
    phone = models.CharField(max_length=15, null=True, blank=True)
    
    # Role e permissões
    role = models.CharField(
        max_length=20, 
        choices=ROLE_CHOICES, 
        default=CUSTOMER
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Configuração de autenticação
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
            models.Index(fields=['role']),
        ]
    
    def clean(self):
        """
        Validações personalizadas
        """
        super().clean()
        
        # RN03: Administradores precisam de CPF
        if self.role in [self.ADMIN, self.ADMIN_MASTER]:
            if not self.cpf:
                raise ValidationError({
                    'cpf': 'CPF é obrigatório para administradores'
                })
            if not self._validate_cpf(self.cpf):
                raise ValidationError({
                    'cpf': 'CPF inválido'
                })
        
        # Clientes não precisam de CPF obrigatoriamente
        if self.role == self.CUSTOMER and self.cpf:
            if not self._validate_cpf(self.cpf):
                raise ValidationError({
                    'cpf': 'CPF inválido'
                })
    
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
        return self.role == self.CUSTOMER
    
    @property
    def is_admin(self):
        return self.role == self.ADMIN
    
    @property
    def is_admin_master(self):
        return self.role == self.ADMIN_MASTER
    
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
    
    # Dados do endereço
    street = models.CharField(max_length=255, verbose_name="Rua")
    number = models.CharField(max_length=20, verbose_name="Número")
    complement = models.CharField(max_length=100, null=True, blank=True, verbose_name="Complemento")
    neighborhood = models.CharField(max_length=100, verbose_name="Bairro")
    city = models.CharField(max_length=100, verbose_name="Cidade")
    state = models.CharField(max_length=2, verbose_name="Estado")
    zip_code = models.CharField(max_length=8, verbose_name="CEP")
    
    # Configurações
    is_default = models.BooleanField(default=False, verbose_name="Endereço padrão")
    
    # Timestamps
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
