from rest_framework import status, viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView
from django.utils import timezone
from datetime import timedelta

from ..models import User, UserSession
from ..serializers import (
    UserRegistrationSerializer,
    AdminRegistrationSerializer,
    UserLoginSerializer,
    AdminLoginSerializer,
    UserSerializer,
    ChangePasswordSerializer
)




class AuthViewSet(viewsets.GenericViewSet):
    permission_classes = [permissions.AllowAny]
    serializer_class = UserSerializer
    
    @action(detail=False, methods=['post'], url_path='register')
    def register_user(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        self._create_session(user, str(refresh), request)
        
        return Response({
            'message': 'Usuário cadastrado com sucesso!',
            'user': UserSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        }, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['post'], url_path='register/admin', 
            permission_classes=[permissions.IsAuthenticated])
    def register_admin(self, request):
        if not request.user.is_admin:
            return Response(
                {'error': 'Apenas administradores podem cadastrar outros administradores.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = AdminRegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        admin = serializer.save()
        
        return Response({
            'message': 'Administrador cadastrado com sucesso!',
            'user': UserSerializer(admin).data,
        }, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['post'], url_path='login')
    def login_user(self, request):
        serializer = UserLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        user.last_login = timezone.now()
        user.save(update_fields=['last_login'])
        refresh = RefreshToken.for_user(user)
        self._create_session(user, str(refresh), request)
        
        return Response({
            'message': 'Login realizado com sucesso!',
            'user': UserSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        }, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['post'], url_path='login/admin')
    def login_admin(self, request):
        serializer = AdminLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        user.last_login = timezone.now()
        user.save(update_fields=['last_login'])
        refresh = RefreshToken.for_user(user)
        self._create_session(user, str(refresh), request)
        
        return Response({
            'message': 'Login de administrador realizado com sucesso!',
            'user': UserSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        }, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['post'], url_path='guest')
    def guest_access(self, request):
        return Response({
            'message': 'Acesso de visitante permitido.',
            'user_type': 'GUEST',
            'restrictions': [
                'Não é possível finalizar compras',
                'Não é possível salvar produtos favoritos',
                'Dados não serão salvos'
            ]
        }, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['post'], url_path='logout',
            permission_classes=[permissions.IsAuthenticated])
    def logout_user(self, request):
        try:
            refresh_token = request.data.get('refresh_token')
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
                
                UserSession.objects.filter(
                    user=request.user,
                    refresh_token=refresh_token
                ).update(is_active=False)
            
            return Response({
                'message': 'Logout realizado com sucesso!'
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'error': 'Erro ao realizar logout.',
                'details': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    def _create_session(self, user, refresh_token, request):
        UserSession.objects.create(
            user=user,
            refresh_token=refresh_token,
            ip_address=self._get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            expires_at=timezone.now() + timedelta(days=7)
        )
    
    def _get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_admin:
            return User.objects.all()
        return User.objects.filter(id=user.id)
    
    @action(detail=False, methods=['get'], url_path='me')
    def get_current_user(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)
    
    @action(detail=False, methods=['patch'], url_path='me/update')
    def update_current_user(self, request):
        serializer = self.get_serializer(
            request.user, 
            data=request.data, 
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({
            'message': 'Perfil atualizado com sucesso!',
            'user': serializer.data
        })
    
    @action(detail=False, methods=['post'], url_path='change-password')
    def change_password(self, request):
        serializer = ChangePasswordSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        user = request.user
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        
        return Response({
            'message': 'Senha alterada com sucesso!'
        }, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['post'], url_path='activate',
            permission_classes=[permissions.IsAuthenticated])
    def activate_user(self, request, pk=None):
        if not request.user.is_admin:
            return Response(
                {'error': 'Apenas administradores podem ativar usuários.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        user = self.get_object()
        user.is_active = True
        user.save()
        
        return Response({
            'message': f'Usuário {user.email} ativado com sucesso!'
        })
    
    @action(detail=True, methods=['post'], url_path='deactivate',
            permission_classes=[permissions.IsAuthenticated])
    def deactivate_user(self, request, pk=None):
        if not request.user.is_admin:
            return Response(
                {'error': 'Apenas administradores podem desativar usuários.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        user = self.get_object()
        
        if user.is_admin and not request.user.is_superuser:
            return Response(
                {'error': 'Apenas superusuários podem desativar administradores.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        user.is_active = False
        user.save()
        
        return Response({
            'message': f'Usuário {user.email} desativado com sucesso!'
        })

class TokenViewSet(viewsets.GenericViewSet):
    permission_classes = [permissions.AllowAny]
    
    @action(detail=False, methods=['get'], url_path='validate',
            permission_classes=[permissions.IsAuthenticated])
    def validate_token(self, request):
        return Response({
            'valid': True,
            'user': UserSerializer(request.user).data
        }, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['post'], url_path='refresh')
    def refresh_token(self, request):
        refresh_token = request.data.get('refresh')
        
        if not refresh_token:
            return Response(
                {'error': 'Refresh token é obrigatório.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            token = RefreshToken(refresh_token)
            return Response({
                'access': str(token.access_token),
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {'error': 'Token inválido ou expirado.', 'details': str(e)},
                status=status.HTTP_401_UNAUTHORIZED
            )

class UserSessionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = UserSession.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_admin:
            return UserSession.objects.all()
        return UserSession.objects.filter(user=user)
    
    @action(detail=False, methods=['get'], url_path='active')
    def active_sessions(self, request):
        sessions = self.get_queryset().filter(
            is_active=True,
            expires_at__gt=timezone.now()
        )
        
        data = [{
            'id': str(session.id),
            'ip_address': session.ip_address,
            'user_agent': session.user_agent,
            'created_at': session.created_at,
            'expires_at': session.expires_at,
        } for session in sessions]
        
        return Response(data)
    
    @action(detail=True, methods=['post'], url_path='revoke')
    def revoke_session(self, request, pk=None):
        session = self.get_object()
        
        if session.user != request.user and not request.user.is_admin:
            return Response(
                {'error': 'Você não tem permissão para revogar esta sessão.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        session.is_active = False
        session.save()
        
        return Response({
            'message': 'Sessão revogada com sucesso!'
        })
