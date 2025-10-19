from rest_framework import status, viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.utils import timezone
from datetime import timedelta

from ..models import User, Address, CUSTOMER, ADMIN, ADMIN_MASTER
from ..serializers import (
    UserListSerializer,
    UserDetailSerializer,
    UserRegistrationSerializer,
    AdminRegistrationSerializer,
    UserUpdateSerializer,
    ChangePasswordSerializer,
    AdminUpdateSerializer,
    AddressSerializer,
)




class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        refresh = RefreshToken.for_user(user)

        return Response({
            'message': 'Usuário cadastrado com sucesso!',
            'user': UserDetailSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        }, status=status.HTTP_201_CREATED)

class RegisterAdminView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        if not request.user.is_admin_master:
            return Response(
                {'error': 'Apenas ADM Master podem cadastrar administradores.'},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = AdminRegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        admin = serializer.save()

        return Response({
            'message': 'Administrador cadastrado com sucesso!',
            'user': UserDetailSerializer(admin).data,
        }, status=status.HTTP_201_CREATED)

class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
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
            return Response(
                {'error': 'Email ou senha inválidos.'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        if not user.check_password(password):
            return Response(
                {'error': 'Email ou senha inválidos.'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        if not user.is_active:
            return Response(
                {'error': 'Esta conta está desativada.'},
                status=status.HTTP_403_FORBIDDEN
            )

        user.last_login = timezone.now()
        user.save(update_fields=['last_login'])
        refresh = RefreshToken.for_user(user)

        return Response({
            'message': 'Login realizado com sucesso!',
            'user': UserDetailSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        }, status=status.HTTP_200_OK)

class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get('refresh_token')
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()

            return Response({
                'message': 'Logout realizado com sucesso!'
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'error': 'Erro ao realizar logout.',
                'details': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

class VerifyTokenView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response({
            'valid': True,
            'user': UserDetailSerializer(request.user).data
        }, status=status.HTTP_200_OK)

class VerifyRoleView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        return Response({
            'role': user.role,
            'is_customer': user.is_customer,
            'is_admin': user.is_admin,
            'is_admin_master': user.is_admin_master,
        }, status=status.HTTP_200_OK)

class RefreshView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
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

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'list':
            return UserListSerializer
        elif self.action == 'retrieve':
            return UserDetailSerializer
        elif self.action == 'partial_update':
            if self.request.user.is_admin_master:
                return AdminUpdateSerializer
            return UserUpdateSerializer
        return UserDetailSerializer

    def get_queryset(self):
        user = self.request.user

        if user.is_admin_master:
            return User.objects.all()
        elif user.is_admin:
            return User.objects.filter(role=CUSTOMER)
        else:
            return User.objects.filter(id=user.id)

    def list(self, request):
        queryset = self.get_queryset()
        role = request.query_params.get('role')
        search = request.query_params.get('search')

        if role:
            queryset = queryset.filter(role=role)

        if search:
            queryset = queryset.filter(
                models.Q(name__icontains=search) |
                models.Q(email__icontains=search)
            )

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        try:
            user = self.get_queryset().get(pk=pk)
        except User.DoesNotExist:
            return Response(
                {'error': 'Usuário não encontrado.'},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = self.get_serializer(user)
        return Response(serializer.data)

    def partial_update(self, request, pk=None):
        try:
            user = self.get_queryset().get(pk=pk)
        except User.DoesNotExist:
            return Response(
                {'error': 'Usuário não encontrado.'},
                status=status.HTTP_404_NOT_FOUND
            )

        if user != request.user and not request.user.is_admin_master:
            return Response(
                {'error': 'Você não tem permissão para atualizar este usuário.'},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = self.get_serializer(
            user,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({
            'message': 'Usuário atualizado com sucesso!',
            'user': serializer.data
        })

    def destroy(self, request, pk=None):
        if not request.user.is_admin_master:
            return Response(
                {'error': 'Apenas ADM Master podem deletar usuários.'},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return Response(
                {'error': 'Usuário não encontrado.'},
                status=status.HTTP_404_NOT_FOUND
            )

        user.delete()

        return Response({
            'message': 'Usuário deletado com sucesso!'
        }, status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'])
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(detail=False, methods=['patch'])
    def me_update(self, request):
        serializer = UserUpdateSerializer(
            request.user,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({
            'message': 'Perfil atualizado com sucesso!',
            'user': UserDetailSerializer(request.user).data
        })

    @action(detail=False, methods=['post'])
    def change_password(self, request):
        serializer = ChangePasswordSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)

        user = request.user
        user.set_password(
            serializer.validated_data['new_password']
        )
        user.save()

        return Response({
            'message': 'Senha alterada com sucesso!'
        }, status=status.HTTP_200_OK)


class AddressViewSet(viewsets.ModelViewSet):
    serializer_class = AddressSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        if user.is_admin_master:
            return Address.objects.all()
        else:
            return Address.objects.filter(user=user)

    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user)

        return Response({
            'message': 'Endereço criado com sucesso!',
            'address': serializer.data
        }, status=status.HTTP_201_CREATED)

    def partial_update(self, request, pk=None):
        try:
            address = self.get_queryset().get(pk=pk)
        except Address.DoesNotExist:
            return Response(
                {'error': 'Endereço não encontrado.'},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = self.get_serializer(
            address,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({
            'message': 'Endereço atualizado com sucesso!',
            'address': serializer.data
        })
