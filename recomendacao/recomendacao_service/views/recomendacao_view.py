from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from datetime import datetime
from ..models import VisualizacaoProduto, InteracaoProduto, AvaliacaoProduto
from ..serializers import (
    VisualizacaoProdutoSerializer,
    InteracaoProdutoSerializer,
    AvaliacaoProdutoSerializer,
    RecomendacaoRequestSerializer,
    RecomendacaoResponseSerializer
)
from ..services import RecomendacaoService
import logging

logger = logging.getLogger(__name__)




class RecomendacaoViewSet(viewsets.ViewSet):
    permission_classes = [AllowAny]
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.service = RecomendacaoService()
    
    @action(detail=False, methods=['get'])
    def obter_recomendacoes(self, request):
        serializer = RecomendacaoRequestSerializer(data=request.query_params)
