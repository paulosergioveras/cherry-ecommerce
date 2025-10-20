from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth import get_user_model
from ..models import Address, CUSTOMER, ADMIN, ADMIN_MASTER

User = get_user_model()


class AddressSerializer(serializers.ModelSerializer):

    class Meta:
        model = Address
        fields = (
            'id',
            'street',
            'number',
            'complement',
            'neighborhood',
            'city',
            'state',
            'zip_code',
            'is_default',
            'created_at',
            'updated_at',
        )
        read_only_fields = ('id', 'created_at', 'updated_at')

class UserListSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = (
            'id',
            'email',
            'name',
            'phone',
            'role',
            'created_at',
        )
        read_only_fields = ('id', 'created_at')

class UserDetailSerializer(serializers.ModelSerializer):
    addresses = AddressSerializer(many=True, read_only=True)

    class Meta:
        model = User
        fields = (
            'id',
            'email',
            'name',
            'cpf',
            'phone',
            'role',
            'addresses',
            'created_at',
            'updated_at',
        )
        read_only_fields = ('id', 'created_at', 'updated_at', 'role')

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password]
    )
    password_confirm = serializers.CharField(
        write_only=True,
        required=True
    )
    phone = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = User
        fields = (
            'email',
            'name',
            'phone',
            'password',
            'password_confirm',
        )

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                'Este email já está cadastrado.'
            )
        return value.lower()

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({
                'password': 'As senhas não coincidem.'
            })
        return attrs

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = User.objects.create_user(
            email=validated_data['email'],
            name=validated_data['name'],
            password=validated_data['password'],
            phone=validated_data.get('phone', ''),
            role=CUSTOMER,
        )
        return user

class AdminRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password]
    )
    password_confirm = serializers.CharField(
        write_only=True,
        required=True
    )
    cpf = serializers.CharField(required=True)
    phone = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = User
        fields = (
            'email',
            'name',
            'cpf',
            'phone',
            'password',
            'password_confirm',
        )

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                'Este email já está cadastrado.'
            )
        return value.lower()

    def validate_cpf(self, value):
        if not User._validate_cpf(value):
            raise serializers.ValidationError('CPF inválido.')

        if User.objects.filter(cpf=value).exists():
            raise serializers.ValidationError(
                'Este CPF já está cadastrado.'
            )
        return value

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({
                'password': 'As senhas não coincidem.'
            })
        return attrs

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = User.objects.create_admin(
            email=validated_data['email'],
            cpf=validated_data['cpf'],
            password=validated_data['password'],
            name=validated_data['name'],
            phone=validated_data.get('phone', ''),
        )
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    phone = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = User
        fields = (
            'name',
            'phone',
        )

    def validate_name(self, value):
        if not value or len(value.strip()) < 2:
            raise serializers.ValidationError(
                'Nome deve ter no mínimo 2 caracteres.'
            )
        return value

class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(
        required=True,
        write_only=True
    )
    new_password = serializers.CharField(
        required=True,
        write_only=True,
        validators=[validate_password]
    )
    new_password_confirm = serializers.CharField(
        required=True,
        write_only=True
    )

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('Senha atual incorreta.')
        return value

    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({
                'new_password': 'As senhas não coincidem.'
            })
        return attrs

class AdminUpdateSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = (
            'name',
            'phone',
            'role',
        )

    def validate_role(self, value):
        if value not in [CUSTOMER, ADMIN, ADMIN_MASTER]:
            raise serializers.ValidationError('Role inválido.')
        return value
