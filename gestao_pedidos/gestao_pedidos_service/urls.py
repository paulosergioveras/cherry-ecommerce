from django.urls import path
from .views import OrderViewSet

urlpatterns = [
    # ==================== PEDIDOS ====================
    # Listar pedidos
    path('orders/', OrderViewSet.as_view({'get': 'list'}), name='orders-list'),
    
    # Meus pedidos
    path('my-orders/', OrderViewSet.as_view({'get': 'my_orders'}), name='orders-my-orders'),
    
    # Estatísticas (admin)
    path('statistics/', OrderViewSet.as_view({'get': 'statistics'}), name='orders-statistics'),
    
    # Criar pedido
    path('create/', OrderViewSet.as_view({'post': 'create'}), name='orders-create'),
    
    # Detalhe do pedido
    path('<uuid:pk>/', OrderViewSet.as_view({'get': 'retrieve'}), name='orders-detail'),
    
    # Atualizar status (admin)
    path('<uuid:pk>/update-status/', OrderViewSet.as_view({'post': 'update_status'}), name='orders-update-status'),
    
    # Cancelar pedido
    path('<uuid:pk>/cancel/', OrderViewSet.as_view({'post': 'cancel'}), name='orders-cancel'),
]
