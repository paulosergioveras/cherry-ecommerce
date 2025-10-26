from django.urls import path
from .views import RecomendacaoViewSet

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
]
