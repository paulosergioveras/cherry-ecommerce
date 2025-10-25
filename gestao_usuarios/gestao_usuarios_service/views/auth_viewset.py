from rest_framework import status, generics, permissions
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from rest_framework.exceptions import ValidationError, AuthenticationFailed
from django.contrib.auth import get_user_model
from django.utils import timezone

from ..serializers import (
    UserRegistrationSerializer,
    UserDetailSerializer,
)

User = get_user_model()


class RegisterView(generics.CreateAPIView):
    """
    Cadastro de novo usuário (cliente)
    POST /api/v1/users/register/
    """
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        print("DEBUG - Request data:", request.data)
        try:
            user_data = request.data
            
            # Valida se email já existe
            is_email_valid = User.objects.filter(email=user_data.get('email', '').lower()).exists()
            if is_email_valid:
                return Response(
                    {'error': 'Email já cadastrado.'},
                    status=status.HTTP_409_CONFLICT
                )
            
            serializer = self.get_serializer(data=user_data)
            serializer.is_valid(raise_exception=True)
            user = serializer.save()
            
            # Gera tokens JWT
            refresh = RefreshToken.for_user(user)
            
            return Response({
                'message': 'Usuário cadastrado com sucesso!',
                'user': UserDetailSerializer(user).data,
                'tokens': {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                }
            }, status=status.HTTP_201_CREATED)
            
        except KeyError as e:
            return Response(
                {'error': f'Campo obrigatório ausente: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except ValidationError as e:
            return Response(
                {'error': e.detail},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'error': 'Erro inesperado ao cadastrar usuário.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class LoginView(generics.GenericAPIView):
    """
    Login de usuários
    POST /api/v1/users/login/
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        try:
            email = request.data.get('email', '').lower()
            password = request.data.get('password', '')

            if not email or not password:
                return Response(
                    {'error': 'Email e senha são obrigatórios.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                raise AuthenticationFailed('Email ou senha inválidos.')

            if not user.check_password(password):
                raise AuthenticationFailed('Email ou senha inválidos.')

            if not user.is_active:
                return Response(
                    {'error': 'Esta conta está desativada.'},
                    status=status.HTTP_403_FORBIDDEN
                )

            # Atualiza último login
            user.last_login = timezone.now()
            user.save(update_fields=['last_login'])

            # Gera tokens JWT
            refresh = RefreshToken.for_user(user)
            
            # Verifica a role do usuário
            role = self._verify_user_role(user)

            return Response({
                'message': 'Login realizado com sucesso!',
                'user': UserDetailSerializer(user).data,
                'user_id': user.id,
                'user_role': role,
                'user_name': user.name,
                'tokens': {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                }
            }, status=status.HTTP_200_OK)

        except KeyError as e:
            return Response(
                {'error': f'Campo obrigatório ausente: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except ValidationError as e:
            return Response(
                {'error': e.detail},
                status=status.HTTP_403_FORBIDDEN
            )
        except AuthenticationFailed as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_401_UNAUTHORIZED
            )
        except Exception as e:
            return Response(
                {'error': 'Erro inesperado ao realizar login.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _verify_user_role(self, user):
        """Verifica e retorna a role do usuário"""
        if user.is_customer:
            return 'customer'
        elif user.is_admin:
            return 'admin'
        elif user.is_admin_master:
            return 'admin_master'
        return None


class LogoutView(generics.GenericAPIView):
    """
    Logout do usuário
    POST /api/v1/users/logout/
    """
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        return None

    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            
            if not refresh_token:
                return Response(
                    {'error': 'Refresh token é obrigatório.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            token = RefreshToken(refresh_token)
            token.blacklist()
            
            return Response(
                {'message': 'Logout realizado com sucesso.'},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {'detail': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class RefreshView(generics.GenericAPIView):
    """
    Atualiza o access token usando o refresh token
    POST /api/v1/users/refresh/
    """
    permission_classes = [permissions.AllowAny]

    def get_serializer_class(self):
        return None

    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            
            if not refresh_token:
                return Response(
                    {'error': 'Refresh token é obrigatório.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            token = RefreshToken(refresh_token)
            
            return Response({
                'access': str(token.access_token),
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {'detail': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class VerifyRoleView(generics.GenericAPIView):
    """
    Verifica a role/permissão do usuário autenticado
    POST /api/v1/users/verify-role/
    """
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        return None

    def post(self, request):
        required_role = request.data.get('role')
        
        if not required_role:
            return Response(
                {"detail": "Parâmetro 'role' é obrigatório"},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = request.user
        has_access = False
        
        # Lógica de permissões hierárquicas
        if required_role == 'customer':
            has_access = user.is_customer or user.is_admin or user.is_admin_master
            
        elif required_role == 'admin':
            has_access = user.is_admin or user.is_admin_master
            
        elif required_role == 'admin_master':
            has_access = user.is_admin_master
            
        else:
            return Response(
                {"detail": "Role inválida especificada"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not has_access:
            return Response(
                {"detail": f"Você não tem privilégios de {required_role}"},
                status=status.HTTP_403_FORBIDDEN
            )

        return Response(
            {
                "detail": "Permissão concedida",
                "user_id": user.id,
                "required_role": required_role,
                "actual_role": self._get_user_role(user)
            },
            status=status.HTTP_200_OK
        )
    
    def _get_user_role(self, user):
        """Retorna a role atual do usuário"""
        if user.is_admin_master:
            return 'admin_master'
        elif user.is_admin:
            return 'admin'
        elif user.is_customer:
            return 'customer'
        return 'unknown'


class VerifyTokenView(generics.GenericAPIView):
    """
    Valida se o token JWT é válido
    POST /api/v1/users/verify-token/
    """
    permission_classes = [permissions.AllowAny]

    def get_serializer_class(self):
        return None

    def post(self, request):
        token = request.data.get('token')
        
        # Se não vier no body, tenta pegar do header
        if not token:
            auth_header = request.headers.get('Authorization')
            if auth_header:
                token = auth_header.split(' ')[-1]
        
        if not token:
            return Response(
                {"detail": "Token é obrigatório no body (token) ou header (Authorization)"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            access_token = AccessToken(token)
            user_id = access_token['user_id']
            user = User.objects.get(id=user_id)

            return Response(
                {
                    "detail": "Token válido",
                    "user_id": user.id,
                    "email": user.email,
                    "name": user.name,
                    "role": user.role,
                    "is_customer": user.is_customer,
                    "is_admin": user.is_admin,
                    "is_admin_master": user.is_admin_master
                },
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {"detail": "Token inválido ou expirado"},
                status=status.HTTP_401_UNAUTHORIZED
            )
