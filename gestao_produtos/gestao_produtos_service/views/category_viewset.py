from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q, Count

from ..models import Category
from ..serializers import (
    CategoryListSerializer,
    CategoryDetailSerializer,
    CategoryCreateUpdateSerializer,
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

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.annotate(
        products_count=Count('products', filter=Q(products__is_active=True))
    )
    permission_classes = [IsAdminOrReadOnly]
    lookup_field = 'slug'
    
    def get_serializer_class(self):
        if self.action == 'list':
            return CategoryListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return CategoryCreateUpdateSerializer
        return CategoryDetailSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        if not (self.request.user.is_authenticated and 
                hasattr(self.request.user, 'is_admin') and
                (self.request.user.is_admin or self.request.user.is_admin_master)):
            queryset = queryset.filter(is_active=True)
        return queryset
    
    def list(self, request):
        queryset = self.get_queryset()
        parent_only = request.query_params.get('parent_only')
        parent_id = request.query_params.get('parent')
        search = request.query_params.get('search')
        
        if parent_only == 'true':
            queryset = queryset.filter(parent__isnull=True)
        
        if parent_id:
            queryset = queryset.filter(parent_id=parent_id)
        
        if search:
            queryset = queryset.filter(name__icontains=search)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        category = serializer.save()
        
        return Response({
            'message': 'Categoria criada com sucesso!',
            'category': CategoryDetailSerializer(category).data
        }, status=status.HTTP_201_CREATED)
    
    def retrieve(self, request, slug=None):
        category = self.get_object()
        serializer = self.get_serializer(category)
        return Response(serializer.data)
    
    def partial_update(self, request, slug=None):
        category = self.get_object()
        serializer = self.get_serializer(
            category,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response({
            'message': 'Categoria atualizada com sucesso!',
            'category': CategoryDetailSerializer(category).data
        })
    
    def destroy(self, request, slug=None):
        category = self.get_object()
        
        if category.products.exists():
            return Response({
                'error': 'Não é possível deletar categoria com produtos associados.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if category.subcategories.exists():
            return Response({
                'error': 'Não é possível deletar categoria com subcategorias.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        category.delete()
        
        return Response({
            'message': 'Categoria deletada com sucesso!'
        }, status=status.HTTP_204_NO_CONTENT)
    
    @action(detail=True, methods=['post'])
    def toggle_active(self, request, slug=None):
        category = self.get_object()
        category.is_active = not category.is_active
        category.save()
        
        status_text = 'ativada' if category.is_active else 'desativada'
        
        return Response({
            'message': f'Categoria {status_text} com sucesso!',
            'is_active': category.is_active
        })
    
    @action(detail=False, methods=['get'])
    def tree(self, request):
        parents = self.get_queryset().filter(parent__isnull=True)
        
        def build_tree(category):
            data = CategoryDetailSerializer(category).data
            subcategories = category.subcategories.filter(is_active=True)
            
            if subcategories.exists():
                data['subcategories'] = [
                    build_tree(sub) for sub in subcategories
                ]
            
            return data
        
        tree_data = [build_tree(cat) for cat in parents]
        
        return Response(tree_data)
