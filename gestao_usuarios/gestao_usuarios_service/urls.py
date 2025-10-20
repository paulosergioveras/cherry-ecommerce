from django.urls import path
from .views import (
    RegisterView,
    RegisterAdminView,
    UserViewSet,
    AddressViewSet,
)

urlpatterns = [
    # ==================== AUTENTICAÇÃO ====================
    # Registro
    path('register/', RegisterView.as_view(), name='register'),
    path('register/admin/', RegisterAdminView.as_view(), name='register-admin'),
    
    
    # ==================== USUÁRIOS - AÇÕES ESPECÍFICAS ====================
    # Visualizar perfil do usuário autenticado
    path('user/me/', UserViewSet.as_view({'get': 'me'}), name='user-me'),
    
    # Atualizar perfil do usuário autenticado
    path('user/update-profile/', UserViewSet.as_view({'patch': 'update_profile'}), name='user-update-profile'),
    
    # Alterar senha
    path('user/change-password/', UserViewSet.as_view({'post': 'change_password'}), name='user-change-password'),
    
    # Listar apenas administradores
    path('user/list-admins/', UserViewSet.as_view({'get': 'list_admins'}), name='list-admins'),
    
    
    # ==================== USUÁRIOS - CRUD ====================
    # Listar todos os usuários
    path('user/', UserViewSet.as_view({'get': 'list'}), name='users-list'),
    
    # Detalhe de um usuário
    path('user/<int:pk>/', UserViewSet.as_view({'get': 'retrieve'}), name='user-detail'),
    
    # Atualizar um usuário
    path('user/<int:pk>/update/', UserViewSet.as_view({'patch': 'partial_update'}), name='user-update'),
    
    # Deletar um usuário
    path('user/<int:pk>/delete/', UserViewSet.as_view({'delete': 'destroy'}), name='user-delete'),
    
    # Ativar usuário
    path('user/<int:pk>/activate/', UserViewSet.as_view({'post': 'activate'}), name='user-activate'),
    
    # Desativar usuário
    path('user/<int:pk>/deactivate/', UserViewSet.as_view({'post': 'deactivate'}), name='user-deactivate'),
    
    
    # ==================== ENDEREÇOS - AÇÕES ESPECÍFICAS ====================
    # Criar novo endereço
    path('addresses/create/', AddressViewSet.as_view({'post': 'create'}), name='address-create'),
    
    
    # ==================== ENDEREÇOS - CRUD ====================
    # Listar endereços
    path('addresses/', AddressViewSet.as_view({'get': 'list'}), name='addresses-list'),
    
    # Detalhe de endereço
    path('addresses/<int:pk>/', AddressViewSet.as_view({'get': 'retrieve'}), name='address-detail'),
    
    # Atualizar endereço
    path('addresses/<int:pk>/update/', AddressViewSet.as_view({'patch': 'partial_update'}), name='address-update'),
    
    # Deletar endereço
    path('addresses/<int:pk>/delete/', AddressViewSet.as_view({'delete': 'destroy'}), name='address-delete'),
]
