from django.urls import path
from .views import RecomendacaoViewSet

urlpatterns = [
    path('obter_recomendacoes/', 
         RecomendacaoViewSet.as_view({'get': 'get_recomendation'}), 
         name='obter-recomendacoes'),
]
