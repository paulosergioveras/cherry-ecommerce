from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from decimal import Decimal

from ..models import Product, ProductImage
from ..serializers import (
    ProductListSerializer,
    ProductDetailSerializer,
    ProductCreateUpdateSerializer,
    ProductStockUpdateSerializer,
    ProductImageSerializer,
)




class IsAdminOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        
        return (
            request.user and 
            request.user.is_authenticated and 
            hasattr(request.user, 'is_admin') and
            (request.user.is_admin or request.user.is_admin_master)
        )

class ProductViewSet(viewsets.ModelViewSet):    
    queryset = Product.objects.select_related('category').prefetch_related('images')
    permission_classes = [IsAdminOrReadOnly]
    lookup_field = 'slug'
    
    def get_serializer_class(self):
        if self.action == 'list':
            return ProductListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return ProductCreateUpdateSerializer
        return ProductDetailSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        if not (self.request.user.is_authenticated and 
                hasattr(self.request.user, 'is_admin') and
                (self.request.user.is_admin or self.request.user.is_admin_master)):
            queryset = queryset.filter(is_active=True)
        
        return queryset
    
    def list(self, request):
        queryset = self.get_queryset()
        category_slug = request.query_params.get('category')
        search = request.query_params.get('search')
        min_price = request.query_params.get('min_price')
        max_price = request.query_params.get('max_price')
        in_stock = request.query_params.get('in_stock')
        is_featured = request.query_params.get('is_featured')
        order_by = request.query_params.get('order_by', '-created_at')
        
        if category_slug:
            queryset = queryset.filter(category__slug=category_slug)
        
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(description__icontains=search) |
                Q(sku__icontains=search)
            )
        
        if min_price:
            try:
                queryset = queryset.filter(price__gte=Decimal(min_price))
            except:
                pass
        
        if max_price:
            try:
                queryset = queryset.filter(price__lte=Decimal(max_price))
            except:
                pass
        
        if in_stock == 'true':
            queryset = queryset.filter(stock__gt=0)
        
        if is_featured == 'true':
            queryset = queryset.filter(is_featured=True)
        
        valid_orders = [
            'price', '-price',
            'name', '-name',
            'created_at', '-created_at',
            'sales_count', '-sales_count'
        ]
        
        if order_by in valid_orders:
            queryset = queryset.order_by(order_by)
        
        page_size = request.query_params.get('page_size', 20)
        try:
            page_size = int(page_size)
            if page_size > 100:
                page_size = 100
        except:
            page_size = 20
        
        # Implementar paginação aqui se necessário
        
        serializer = self.get_serializer(
            queryset,
            many=True,
            context={'request': request}
        )
        return Response(serializer.data)
    
    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        product = serializer.save()
        
        return Response({
            'message': 'Produto criado com sucesso!',
            'product': ProductDetailSerializer(
                product,
                context={'request': request}
            ).data
        }, status=status.HTTP_201_CREATED)
    
    def retrieve(self, request, slug=None):
        product = self.get_object()
        product.increment_views()
        
        serializer = self.get_serializer(
            product,
            context={'request': request}
        )
        return Response(serializer.data)
    
    def partial_update(self, request, slug=None):
        product = self.get_object()
        serializer = self.get_serializer(
            product,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response({
            'message': 'Produto atualizado com sucesso!',
            'product': ProductDetailSerializer(
                product,
                context={'request': request}
            ).data
        })
    
    def destroy(self, request, slug=None):
        product = self.get_object()

        if product.order_items.exists():
            return Response({
                 'error': 'Não é possível deletar produto com pedidos.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        product.delete()
        
        return Response({
            'message': 'Produto deletado com sucesso!'
        }, status=status.HTTP_204_NO_CONTENT)
    
    @action(detail=True, methods=['post'])
    def toggle_active(self, request, slug=None):
        product = self.get_object()
        product.is_active = not product.is_active
        product.save()
        
        status_text = 'ativado' if product.is_active else 'desativado'
        
        return Response({
            'message': f'Produto {status_text} com sucesso!',
            'is_active': product.is_active
        })
    
    @action(detail=True, methods=['post'])
    def toggle_featured(self, request, slug=None):
        product = self.get_object()
        product.is_featured = not product.is_featured
        product.save()
        
        status_text = 'adicionado aos destaques' if product.is_featured else 'removido dos destaques'
        
        return Response({
            'message': f'Produto {status_text}!',
            'is_featured': product.is_featured
        })
    
    @action(detail=True, methods=['post'])
    def update_stock(self, request, slug=None):
        product = self.get_object()
        serializer = ProductStockUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        quantity = serializer.validated_data['quantity']
        operation = serializer.validated_data['operation']
        
        try:
            if operation == 'add':
                product.increase_stock(quantity)
                message = f'{quantity} unidades adicionadas ao estoque.'
            else:
                product.decrease_stock(quantity)
                message = f'{quantity} unidades removidas do estoque.'
            
            return Response({
                'message': message,
                'current_stock': product.stock
            })
        except ValueError as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def featured(self, request):
        queryset = self.get_queryset().filter(
            is_featured=True,
            is_active=True
        )
        
        serializer = self.get_serializer(
            queryset,
            many=True,
            context={'request': request}
        )
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def best_sellers(self, request):
        queryset = self.get_queryset().filter(
            is_active=True,
            sales_count__gt=0
        ).order_by('-sales_count')[:10]
        
        serializer = self.get_serializer(
            queryset,
            many=True,
            context={'request': request}
        )
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def add_image(self, request, slug=None):
        product = self.get_object()
        serializer = ProductImageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(product=product)
        
        return Response({
            'message': 'Imagem adicionada com sucesso!',
            'image': serializer.data
        }, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['delete'], url_path='remove-image/(?P<image_id>[0-9]+)')
    def remove_image(self, request, slug=None, image_id=None):
        product = self.get_object()
        
        try:
            image = product.images.get(id=image_id)
            image.delete()
            
            return Response({
                'message': 'Imagem removida com sucesso!'
            }, status=status.HTTP_204_NO_CONTENT)
        except ProductImage.DoesNotExist:
            return Response({
                'error': 'Imagem não encontrada.'
            }, status=status.HTTP_404_NOT_FOUND)
