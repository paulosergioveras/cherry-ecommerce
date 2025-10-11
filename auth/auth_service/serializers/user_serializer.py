from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from ..models import User
import re


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer para registro de novos usuários"""
    
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True, required=True)
    
    class Meta:
        model = User
        fields = ('email', 'name', 'password', 'password_confirm', 'user_type')
        extra_kwargs = {
            'user_type': {'default': 'CUSTOMER'}
        }
    
    def validate_email(self, value):
        """Valida o formato do email"""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Este email já está cadastrado.")
        return value.lower()
    
    def validate(self, attrs):
        """Valida se as senhas coincidem"""
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({"password": "As senhas não coincidem."})
        return attrs
    
    def create(self, validated_data):
        """Cria um novo usuário"""
        validated_data.pop('password_confirm')
        user = User.objects.create_user(**validated_data)
        return user


class AdminRegistrationSerializer(serializers.ModelSerializer):
    """Serializer para registro de administradores"""
    
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True, required=True)
    cpf = serializers.CharField(required=True)
    
    class Meta:
        model = User
        fields = ('email', 'name', 'cpf', 'password', 'password_confirm')
    
    def validate_cpf(self, value):
        """Valida o CPF"""
        # Remove caracteres não numéricos
        cpf = re.sub(r'\D', '', value)
        
        if len(cpf) != 11:
            raise serializers.ValidationError("CPF deve ter 11 dígitos.")
        
        if User.objects.filter(cpf=cpf).exists():
            raise serializers.ValidationError("Este CPF já está cadastrado.")
        
        return cpf
    
    def validate(self, attrs):
        """Valida se as senhas coincidem"""
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({"password": "As senhas não coincidem."})
        return attrs
    
    def create(self, validated_data):
        """Cria um novo administrador"""
        validated_data.pop('password_confirm')
        validated_data['user_type'] = 'ADMIN'
        validated_data['is_admin'] = True
        validated_data['is_staff'] = True
        
        user = User.objects.create_user(**validated_data)
        return user


class UserLoginSerializer(serializers.Serializer):
    """Serializer para login de usuários"""
    
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, write_only=True)
    
    def validate(self, attrs):
        """Valida as credenciais do usuário"""
        email = attrs.get('email', '').lower()
        password = attrs.get('password', '')
        
        user = authenticate(username=email, password=password)
        
        if not user:
            raise serializers.ValidationError("Email ou senha inválidos.")
        
        if not user.is_active:
            raise serializers.ValidationError("Esta conta está desativada.")
        
        if user.user_type != 'CUSTOMER':
            raise serializers.ValidationError("Use o login de administrador.")
        
        attrs['user'] = user
        return attrs


class AdminLoginSerializer(serializers.Serializer):
    """Serializer para login de administradores"""
    
    cpf = serializers.CharField(required=True)
    password = serializers.CharField(required=True, write_only=True)
    
    def validate(self, attrs):
        """Valida as credenciais do administrador"""
        cpf = re.sub(r'\D', '', attrs.get('cpf', ''))
        password = attrs.get('password', '')
        
        try:
            user = User.objects.get(cpf=cpf)
        except User.DoesNotExist:
            raise serializers.ValidationError("CPF ou senha inválidos.")
        
        if not user.check_password(password):
            raise serializers.ValidationError("CPF ou senha inválidos.")
        
        if not user.is_active:
            raise serializers.ValidationError("Esta conta está desativada.")
        
        if user.user_type != 'ADMIN':
            raise serializers.ValidationError("Este usuário não é um administrador.")
        
        attrs['user'] = user
        return attrs


class UserSerializer(serializers.ModelSerializer):
    """Serializer para exibição de dados do usuário"""
    
    class Meta:
        model = User
        fields = ('id', 'email', 'name', 'user_type', 'date_joined', 'last_login')
        read_only_fields = ('id', 'date_joined', 'last_login')


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer para mudança de senha"""
    
    old_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(required=True, write_only=True, validators=[validate_password])
    new_password_confirm = serializers.CharField(required=True, write_only=True)
    
    def validate_old_password(self, value):
        """Valida a senha antiga"""
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Senha atual incorreta.")
        return value
    
    def validate(self, attrs):
        """Valida se as novas senhas coincidem"""
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({"new_password": "As senhas não coincidem."})
        return attrs
