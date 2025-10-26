from django.urls import path
from .routers import(
    UsuariosRouter,
    PedidosRouter,
    ProdutosRouter,
    NotificacaoRouter,
    PagamentoRouter,
    RecomendacaoRouter
)

urlpatterns = [
    path('gestao_usuarios/', UsuariosRouter.as_view(), name='gestao_usuarios-root'),
    path('gestao_usuarios/<path:path>', UsuariosRouter.as_view(), name='gestao_usuarios-proxy'),

    path('gestao_pedidos/', PedidosRouter.as_view(), name='gestao_pedidos-root'),
    path('gestao_pedidos/<path:path>', PedidosRouter.as_view(), name='gestao_pedidos-proxy'),
   
    path('gestao_produtos/', ProdutosRouter.as_view(), name='gestao_produtos-root'),
    path('gestao_produtos/<path:path>', ProdutosRouter.as_view(), name='gestao_produtos-proxy'),
    
    path('notificacao/', NotificacaoRouter.as_view(), name='notificacao-root'),
    path('notificacao/<path:path>', NotificacaoRouter.as_view(), name='notificacao-proxy'),

    path('pagamento/', PagamentoRouter.as_view(), name='pagamento-root'),
    path('pagamento/<path:path>', PagamentoRouter.as_view(), name='pagamento-proxy'),

    path('recomendacao/', RecomendacaoRouter.as_view(), name='recomendacao-root'),
    path('recomendacao/<path:path>', RecomendacaoRouter.as_view(), name='recomendacao-proxy'),
]
