from rest_framework import status, viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from django.db import models

from ..models import Address
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

User = get_user_model() 

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
            # Admins can see only customers (users that are not admins)
            return User.objects.filter(is_admin=False, is_admin_master=False)
        else:
            return User.objects.filter(id=user.id)

    def list(self, request):
        # Always list all users regardless of caller role
        queryset = User.objects.all()
        role = request.query_params.get('role')
        search = request.query_params.get('search')

        if role:
            # role query param supports: customer, admin, admin_master
            if role == 'customer':
                queryset = queryset.filter(is_admin=False, is_admin_master=False)
            elif role == 'admin':
                queryset = queryset.filter(is_admin=True, is_admin_master=False)
            elif role == 'admin_master':
                queryset = queryset.filter(is_admin_master=True)
            else:
                # invalid role value -> no results
                queryset = queryset.none()

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
