from django.urls import path
from .views import NotificationViewSet, NotificationPreferenceViewSet

urlpatterns = [
    # ==================== NOTIFICAÇÕES ====================
    # Listar notificações
    path('list/', NotificationViewSet.as_view({'get': 'list'}), name='notifications-list'),
    
    # Contador de não lidas
    path('unread-count/', NotificationViewSet.as_view({'get': 'unread_count'}), name='notifications-unread-count'),
    
    # Estatísticas (admin)
    path('statistics/', NotificationViewSet.as_view({'get': 'statistics'}), name='notifications-statistics'),
    
    # Criar notificação (admin)
    path('create/', NotificationViewSet.as_view({'post': 'create'}), name='notifications-create'),
    
    # Enviar via template
    path('send-from-template/', NotificationViewSet.as_view({'post': 'send_from_template'}), name='notifications-send-from-template'),
    
    # Marcar múltiplas como lidas
    path('mark-multiple-as-read/', NotificationViewSet.as_view({'post': 'mark_multiple_as_read'}), name='notifications-mark-multiple-as-read'),
    
    # Detalhe da notificação
    path('<uuid:pk>/', NotificationViewSet.as_view({'get': 'retrieve'}), name='notifications-detail'),
    
    # Marcar como lida
    path('<uuid:pk>/mark-as-read/', NotificationViewSet.as_view({'post': 'mark_as_read'}), name='notifications-mark-as-read'),
    
    # Reenviar (admin)
    path('<uuid:pk>/retry/', NotificationViewSet.as_view({'post': 'retry'}), name='notifications-retry'),
    
    
    # ==================== PREFERÊNCIAS ====================
    # Minhas preferências
    path('preferences/my-preferences/', NotificationPreferenceViewSet.as_view({'get': 'my_preferences', 'put': 'my_preferences'}), name='preferences-my-preferences'),
]
