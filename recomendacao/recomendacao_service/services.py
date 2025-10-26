#import requests
from datetime import datetime, timedelta
from django.conf import settings
from django.core.cache import cache
from django.db.models import Count, Q, Avg
from .models import VisualizacaoProduto, InteracaoProduto, AvaliacaoProduto, RecomendacaoGerada
import logging

logger = logging.getLogger(__name__)




class MicroserviceClient:
    @staticmethod
    def get_produtos(ids=None, categoria_id=None, limit=10):
        try:
            url = f"{settings.GESTAO_PRODUTOS_URL}/api/v1/produtos/"
            params = {'limit': limit}
            
            if ids:
                params['ids'] = ','.join(map(str, ids))
            if categoria_id:
                params['categoria_id'] = categoria_id
            
            response = requests.get(url, params=params, timeout=5)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Erro ao buscar produtos: {e}")
            return []
    
    @staticmethod
    def get_produto_detalhes(produto_id):
        try:
            url = f"{settings.GESTAO_PRODUTOS_URL}/api/v1/produtos/{produto_id}/"
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Erro ao buscar detalhes do produto {produto_id}: {e}")
            return None
    
    @staticmethod
    def get_pedidos_usuario(usuario_id):
        try:
            url = f"{settings.GESTAO_PEDIDOS_URL}/api/v1/orders/"
            params = {'usuario_id': usuario_id}
            response = requests.get(url, params=params, timeout=5)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Erro ao buscar pedidos do usuário {usuario_id}: {e}")
            return []

class RecomendacaoService:
    def __init__(self):
        self.client = MicroserviceClient()
    
    def registrar_visualizacao(self, usuario_id, produto_id):
        VisualizacaoProduto.objects.create(
            usuario_id=usuario_id,
            produto_id=produto_id
        )
        
        InteracaoProduto.objects.create(
            usuario_id=usuario_id,
            produto_id=produto_id,
            tipo='VIEW',
            peso=1
        )
    
    def registrar_interacao(self, usuario_id, produto_id, tipo, peso=None):
        pesos_padrao = {
            'VIEW': 1,
            'CART': 3,
            'PURCHASE': 5,
            'FAVORITE': 4
        }
        
        if peso is None:
            peso = pesos_padrao.get(tipo, 1)
        
        InteracaoProduto.objects.create(
            usuario_id=usuario_id,
            produto_id=produto_id,
            tipo=tipo,
            peso=peso
        )
        
        self._limpar_cache_usuario(usuario_id)
    
    def get_recomendacoes_populares(self, limite=10):
        cache_key = f'recomendacao:popular:{limite}'
        cached = cache.get(cache_key)
        
        if cached:
            return cached
        
        data_limite = datetime.now() - timedelta(days=30)
        
        produtos_populares = (
            InteracaoProduto.objects
            .filter(criado_em__gte=data_limite)
            .values('produto_id')
            .annotate(
                total_interacoes=Count('id'),
                peso_total=Count('peso')
            )
            .order_by('-peso_total', '-total_interacoes')[:limite]
        )
        
        produto_ids = [p['produto_id'] for p in produtos_populares]
        produtos = self.client.get_produtos(ids=produto_ids)
        
        cache.set(cache_key, produtos, 300)
        return produtos
    
    def get_recomendacoes_similares(self, produto_id, limite=10):
        cache_key = f'recomendacao:similar:{produto_id}:{limite}'
        cached = cache.get(cache_key)
        
        if cached:
            return cached
        
        produto = self.client.get_produto_detalhes(produto_id)
        if not produto:
            return []
        
        categoria_id = produto.get('categoria_id')
        if not categoria_id:
            return []
        
        produtos = self.client.get_produtos(categoria_id=categoria_id, limit=limite + 1)
        
        produtos = [p for p in produtos if p.get('id') != produto_id][:limite]
        
        cache.set(cache_key, produtos, 600)
        return produtos
    
    def get_recomendacoes_personalizadas(self, usuario_id, limite=10):
        cache_key = f'recomendacao:personalizado:{usuario_id}:{limite}'
        cached = cache.get(cache_key)
        
        if cached:
            return cached
        
        data_limite = datetime.now() - timedelta(days=60)
        
        interacoes = (
            InteracaoProduto.objects
            .filter(usuario_id=usuario_id, criado_em__gte=data_limite)
            .values('produto_id')
            .annotate(score=Count('peso'))
            .order_by('-score')[:5]
        )
        
        if not interacoes:
            return self.get_recomendacoes_populares(limite)
        
        recomendacoes = []
        produto_ids_usados = set()
        
        for interacao in interacoes:
            produto_id = interacao['produto_id']
            similares = self.get_recomendacoes_similares(produto_id, limite=3)
            
            for produto in similares:
                pid = produto.get('id')
                if pid not in produto_ids_usados and pid != produto_id:
                    recomendacoes.append(produto)
                    produto_ids_usados.add(pid)
                
                if len(recomendacoes) >= limite:
                    break
            
            if len(recomendacoes) >= limite:
                break
        
        if len(recomendacoes) < limite:
            populares = self.get_recomendacoes_populares(limite - len(recomendacoes))
            for produto in populares:
                if produto.get('id') not in produto_ids_usados:
                    recomendacoes.append(produto)
        
        cache.set(cache_key, recomendacoes[:limite], 300)
        return recomendacoes[:limite]
    
    def get_recomendacoes_categoria(self, categoria_id, limite=10):
        cache_key = f'recomendacao:categoria:{categoria_id}:{limite}'
        cached = cache.get(cache_key)
        
        if cached:
            return cached
        
        produtos = self.client.get_produtos(categoria_id=categoria_id, limit=limite)
        cache.set(cache_key, produtos, 600)
        return produtos
    
    def get_recomendacoes_carrinho(self, produto_ids, limite=10):
        if not produto_ids:
            return self.get_recomendacoes_populares(limite)
        
        cache_key = f'recomendacao:carrinho:{"-".join(map(str, produto_ids))}:{limite}'
        cached = cache.get(cache_key)
        
        if cached:
            return cached
        
        recomendacoes = []
        produto_ids_usados = set(produto_ids)
        
        for produto_id in produto_ids:
            similares = self.get_recomendacoes_similares(produto_id, limite=3)
            
            for produto in similares:
                pid = produto.get('id')
                if pid not in produto_ids_usados:
                    recomendacoes.append(produto)
                    produto_ids_usados.add(pid)
                
                if len(recomendacoes) >= limite:
                    break
            
            if len(recomendacoes) >= limite:
                break
        
        cache.set(cache_key, recomendacoes[:limite], 300)
        return recomendacoes[:limite]
    
    def _limpar_cache_usuario(self, usuario_id):
        cache_keys = [
            f'recomendacao:personalizado:{usuario_id}:*',
        ]
        for key in cache_keys:
            cache.delete(key)
    
    def avaliar_produto(self, usuario_id, produto_id, nota, comentario=''):
        avaliacao, created = AvaliacaoProduto.objects.update_or_create(
            usuario_id=usuario_id,
            produto_id=produto_id,
            defaults={
                'nota': nota,
                'comentario': comentario
            }
        )
        
        self.registrar_interacao(usuario_id, produto_id, 'PURCHASE', peso=nota)
        
        return avaliacao
    
    def get_avaliacoes_produto(self, produto_id):
        avaliacoes = AvaliacaoProduto.objects.filter(produto_id=produto_id)
        
        return {
            'produto_id': produto_id,
            'total_avaliacoes': avaliacoes.count(),
            'nota_media': avaliacoes.aggregate(Avg('nota'))['nota__avg'] or 0,
            'avaliacoes': list(avaliacoes.values())
        }
