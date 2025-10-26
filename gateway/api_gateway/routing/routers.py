from .router import MicroserviceRouter
from api_gateway.services import *




class UsuariosRouter(MicroserviceRouter):
    service_url = gestao_usuarios.GESTAO_USUARIOS_SERVICE_URL
    service_prefix = 'api/v1/users'


class PedidosRouter(MicroserviceRouter):
    service_url = gestao_pedidos.GESTAO_PEDIDOS_SERVICE_URL
    service_prefix = 'api/v1/orders/'


class ProdutosRouter(MicroserviceRouter):
    service_url = gestao_produtos.GESTAO_PRODUTOS_SERVICE_URL
    service_prefix = 'api/v1/produtos/'


class NotificacaoRouter(MicroserviceRouter):
    service_url = notificacao.NOTIFICACAO_SERVICE_URL 
    service_prefix = 'api/v1/notificacao/'

class PagamentoRouter(MicroserviceRouter):
    service_url = pagamento.PAGAMENTO_SERVICE_URL
    service_prefix = 'api/v1/payments/'

class RecomendacaoRouter(MicroserviceRouter):
    service_url = recomendacao.RECOMENDACAO_SERVICE_URL
    service_prefix = 'api/v1/recomendacao/'
