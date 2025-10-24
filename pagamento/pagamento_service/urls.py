from django.urls import path
from .views import PaymentViewSet

urlpatterns = [
    # ==================== PAGAMENTOS ====================
    # Listar pagamentos
    path('list/', PaymentViewSet.as_view({'get': 'list'}), name='payments-list'),
    
    # Estatísticas (admin)
    path('statistics/', PaymentViewSet.as_view({'get': 'statistics'}), name='payments-statistics'),
    
    # Processar pagamento
    path('create/', PaymentViewSet.as_view({'post': 'create'}), name='payments-create'),
    
    # Detalhe do pagamento
    path('<uuid:pk>/', PaymentViewSet.as_view({'get': 'retrieve'}), name='payments-detail'),
    
    # Atualizar status (admin)
    path('<uuid:pk>/update-status/', PaymentViewSet.as_view({'post': 'update_status'}), name='payments-update-status'),
    
    # Solicitar reembolso
    path('<uuid:pk>/request-refund/', PaymentViewSet.as_view({'post': 'request_refund'}), name='payments-request-refund'),
]
