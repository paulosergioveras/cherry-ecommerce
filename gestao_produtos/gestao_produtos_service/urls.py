from django.urls import path
from .views import CategoryViewSet, ProductViewSet

urlpatterns = [
    # ==================== CATEGORIAS ====================
    # Listar categorias
    path('categories/', CategoryViewSet.as_view({'get': 'list'}), name='categories-list'),
    
    # Árvore hierárquica de categorias
    path('categories/tree/', CategoryViewSet.as_view({'get': 'tree'}), name='categories-tree'),
    
    # Criar categoria
    path('categories/create/', CategoryViewSet.as_view({'post': 'create'}), name='categories-create'),
    
    # Detalhe de categoria
    path('categories/<slug:slug>/', CategoryViewSet.as_view({'get': 'retrieve'}), name='categories-detail'),
    
    # Atualizar categoria
    path('categories/<slug:slug>/update/', CategoryViewSet.as_view({'patch': 'partial_update'}), name='categories-update'),
    
    # Deletar categoria
    path('categories/<slug:slug>/delete/', CategoryViewSet.as_view({'delete': 'destroy'}), name='categories-delete'),
    
    # Ativar/desativar categoria
    path('categories/<slug:slug>/toggle-active/', CategoryViewSet.as_view({'post': 'toggle_active'}), name='categories-toggle-active'),
    
    
    # ==================== PRODUTOS ====================
    # Listar produtos
    path('', ProductViewSet.as_view({'get': 'list'}), name='products-list'),
    
    # Produtos em destaque
    path('featured/', ProductViewSet.as_view({'get': 'featured'}), name='products-featured'),
    
    # Mais vendidos
    path('best-sellers/', ProductViewSet.as_view({'get': 'best_sellers'}), name='products-best-sellers'),
    
    # Criar produto
    path('create/', ProductViewSet.as_view({'post': 'create'}), name='products-create'),
    
    # Detalhe de produto
    path('<slug:slug>/', ProductViewSet.as_view({'get': 'retrieve'}), name='products-detail'),
    
    # Atualizar produto
    path('<slug:slug>/update/', ProductViewSet.as_view({'patch': 'partial_update'}), name='products-update'),
    
    # Deletar produto
    path('<slug:slug>/delete/', ProductViewSet.as_view({'delete': 'destroy'}), name='products-delete'),
    
    # Ativar/desativar produto
    path('<slug:slug>/toggle-active/', ProductViewSet.as_view({'post': 'toggle_active'}), name='products-toggle-active'),
    
    # Adicionar/remover dos destaques
    path('<slug:slug>/toggle-featured/', ProductViewSet.as_view({'post': 'toggle_featured'}), name='products-toggle-featured'),
    
    # Atualizar estoque
    path('<slug:slug>/update-stock/', ProductViewSet.as_view({'post': 'update_stock'}), name='products-update-stock'),
    
    # Adicionar imagem
    path('<slug:slug>/add-image/', ProductViewSet.as_view({'post': 'add_image'}), name='products-add-image'),
    
    # Remover imagem
    path('<slug:slug>/remove-image/<int:image_id>/', ProductViewSet.as_view({'delete': 'remove_image'}), name='products-remove-image'),
]
