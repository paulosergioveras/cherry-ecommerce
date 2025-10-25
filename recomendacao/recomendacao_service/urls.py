from django.urls import path
from .views import RecomendacaoViewSet, AvaliacaoViewSet

urlpatterns = [
    path('obter_recomendacoes/', 
         RecomendacaoViewSet.as_view({'get': 'obter_recomendacoes'}), 
         name='obter-recomendacoes'),
    
    path('registrar_visualizacao/', 
         RecomendacaoViewSet.as_view({'post': 'registrar_visualizacao'}), 
         name='registrar-visualizacao'),
    
    path('registrar_interacao/', 
         RecomendacaoViewSet.as_view({'post': 'registrar_interacao'}), 
         name='registrar-interacao'),
    
    # Avaliações
    path('avaliacoes/', 
         AvaliacaoViewSet.as_view({'get': 'list', 'post': 'create'}), 
         name='avaliacoes'),
    
    path('avaliacoes/<int:pk>/', 
         AvaliacaoViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}), 
         name='avaliacao-detail'),
    
    path('avaliacoes/por_produto/', 
         AvaliacaoViewSet.as_view({'get': 'por_produto'}), 
         name='avaliacoes-por-produto'),
]
