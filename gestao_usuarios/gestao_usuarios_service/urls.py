from django.urls import path
from .views import (
    RegisterView,
    RegisterAdminView,
    LoginView,
    LogoutView,
    RefreshView,
    VerifyRoleView,
    VerifyTokenView,
    UserViewSet,
    AddressViewSet,
)

urlpatterns = [
    # ==================== AUTENTICAÇÃO ====================
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('verify-role/', VerifyRoleView.as_view(), name='verify-role'),
    path('verify-token/', VerifyTokenView.as_view(), name='verify-token'),
    path('refresh/', RefreshView.as_view(), name='refresh'),
    
    # Registro de admin (apenas admin master)
    path('register/admin/', RegisterAdminView.as_view(), name='register-admin'),
    
    
    # ==================== USUÁRIOS - AÇÕES ESPECÍFICAS ====================
    # Perfil do usuário autenticado
    path('users/me/', UserViewSet.as_view({'get': 'me'}), name='users-me'),
    path('users/me/update/', UserViewSet.as_view({'patch': 'me_update'}), name='users-me-update'),
    path('users/change-password/', UserViewSet.as_view({'post': 'change_password'}), name='users-change-password'),
    
    
    # ==================== USUÁRIOS - CRUD ====================
    path('users/', UserViewSet.as_view({'get': 'list'}), name='users-list'),
    path('users/<int:pk>/', UserViewSet.as_view({'get': 'retrieve'}), name='users-detail'),
    path('users/<int:pk>/update/', UserViewSet.as_view({'patch': 'partial_update'}), name='users-update'),
    path('users/<int:pk>/delete/', UserViewSet.as_view({'delete': 'destroy'}), name='users-delete'),
    
    
    # ==================== ENDEREÇOS ====================
    path('addresses/', AddressViewSet.as_view({'get': 'list'}), name='addresses-list'),
    path('addresses/create/', AddressViewSet.as_view({'post': 'create'}), name='addresses-create'),
    path('addresses/<int:pk>/', AddressViewSet.as_view({'get': 'retrieve'}), name='addresses-detail'),
    path('addresses/<int:pk>/update/', AddressViewSet.as_view({'patch': 'partial_update'}), name='addresses-update'),
    path('addresses/<int:pk>/delete/', AddressViewSet.as_view({'delete': 'destroy'}), name='addresses-delete'),
]
