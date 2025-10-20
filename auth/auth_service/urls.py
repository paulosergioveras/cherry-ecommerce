from django.urls import path
from .views import (
    RegisterView,
    RegisterAdminView,
    LoginView,
    LoginAdminView,
    GuestAccessView,
    LogoutView,
    UserViewSet,
    ChangePasswordView,
    TokenViewSet,
    UserSessionViewSet,
)

"""
urlpatterns = [

    path('register/', RegisterView.as_view(), name='register'),
    path('register/admin/', RegisterAdminView.as_view(), name='register-admin'),

    path('login/', LoginView.as_view(), name='login'),
    path('login/admin/', LoginAdminView.as_view(), name='login-admin'),
    path('guest/', GuestAccessView.as_view(), name='guest-access'),
    path('logout/', LogoutView.as_view(), name='logout'),
    
    path('token/validate/', TokenViewSet.as_view({'get': 'validate_token'}), name='token-validate'),
    path('token/refresh/', TokenViewSet.as_view({'post': 'refresh_token'}), name='token-refresh'),
    
    path('users/', UserViewSet.as_view({'get': 'list'}), name='users-list'),
    path('users/<uuid:pk>/', UserViewSet.as_view({'get': 'retrieve'}), name='user-detail'),
    path('users/<uuid:pk>/update/', UserViewSet.as_view({'patch': 'partial_update'}), name='user-update'),
    path('users/<uuid:pk>/delete/', UserViewSet.as_view({'delete': 'destroy'}), name='user-delete'),
    
    path('users/me/', UserViewSet.as_view({'get': 'get_current_user'}), name='user-me'),
    path('users/me/update/', UserViewSet.as_view({'patch': 'update_current_user'}), name='user-me-update'),
    
    path('users/change-password/', ChangePasswordView.as_view(), name='change-password'),
    path('users/<uuid:pk>/activate/', UserViewSet.as_view({'post': 'activate_user'}), name='user-activate'),
    path('users/<uuid:pk>/deactivate/', UserViewSet.as_view({'post': 'deactivate_user'}), name='user-deactivate'),
    
    path('sessions/', UserSessionViewSet.as_view({'get': 'list'}), name='sessions-list'),
    path('sessions/<uuid:pk>/', UserSessionViewSet.as_view({'get': 'retrieve'}), name='session-detail'),
    path('sessions/active/', UserSessionViewSet.as_view({'get': 'active_sessions'}), name='sessions-active'),
    path('sessions/<uuid:pk>/revoke/', UserSessionViewSet.as_view({'post': 'revoke_session'}), name='session-revoke'),
]
"""