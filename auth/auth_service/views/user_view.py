from rest_framework import status, viewsets, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.utils import timezone
from datetime import timedelta

from ..models import User, UserSession
from ..serializers import (
    UserRegistrationSerializer,
    AdminRegistrationSerializer,
    UserLoginSerializer,
    AdminLoginSerializer,
    UserSerializer,
    ChangePasswordSerializer,
    UserSessionSerializer
)




class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
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

class RegisterAdminView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def post(self, request):
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

class LoginView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
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

class LoginAdminView(APIView):
    permission_classes = [permissions.AllowAny]
    def post(self, request):
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

class GuestAccessView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        return Response({
            'message': 'Acesso de visitante permitido.',
            'user_type': 'GUEST',
            'restrictions': [
                'Não é possível finalizar compras',
                'Não é possível salvar produtos favoritos',
                'Dados não serão salvos'
            ]
        }, status=status.HTTP_200_OK)

class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def post(self, request):
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

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'pk'
    
    def get_queryset(self):
        user = self.request.user
        if user.is_admin:
            return User.objects.all()
        return User.objects.filter(id=user.id)
    
    def list(self, request):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    def retrieve(self, request, pk=None):
        user = self.get_object()
        serializer = self.get_serializer(user)
        return Response(serializer.data)
    
    def partial_update(self, request, pk=None):
        user = self.get_object()
        if user != request.user and not request.user.is_admin:
            return Response(
                {'error': 'Você não tem permissão para atualizar este usuário.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = self.get_serializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response({
            'message': 'Usuário atualizado com sucesso!',
            'user': serializer.data
        })
    
    def destroy(self, request, pk=None):
        if not request.user.is_admin:
            return Response(
                {'error': 'Apenas administradores podem deletar usuários.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        user = self.get_object()
        user.delete()
        
        return Response({
            'message': 'Usuário deletado com sucesso!'
        }, status=status.HTTP_204_NO_CONTENT)
    
    def get_current_user(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)
    
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

class ChangePasswordView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
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

class TokenViewSet(viewsets.ViewSet):
    permission_classes = [permissions.AllowAny]
    
    def validate_token(self, request):
        if not request.user.is_authenticated:
            return Response(
                {'valid': False, 'error': 'Token inválido ou expirado.'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        return Response({
            'valid': True,
            'user': UserSerializer(request.user).data
        }, status=status.HTTP_200_OK)
    
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
    serializer_class = UserSessionSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'pk'
    
    def get_queryset(self):
        user = self.request.user
        if user.is_admin:
            return UserSession.objects.all()
        return UserSession.objects.filter(user=user)
    
    def list(self, request):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    def retrieve(self, request, pk=None):
        session = self.get_object()
        serializer = self.get_serializer(session)
        return Response(serializer.data)
    
    def active_sessions(self, request):
        sessions = self.get_queryset().filter(
            is_active=True,
            expires_at__gt=timezone.now()
        )
        
        serializer = self.get_serializer(sessions, many=True)
        return Response(serializer.data)
    
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
