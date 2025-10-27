from rest_framework import serializers
from ..models import Category




class CategoryListSerializer(serializers.ModelSerializer):
    products_count = serializers.IntegerField(source='products_count_annotated',read_only=True)
    
    class Meta:
        model = Category
        fields = '__all__'
        read_only_fields = ('id', 'slug', 'products_count')

class SubcategorySerializer(serializers.ModelSerializer):
    products_count = serializers.IntegerField(source='products_count_annotated', read_only=True)
    
    class Meta:
        model = Category
        fields = '__all__'
        read_only_fields = ('id', 'slug', 'products_count')

class CategoryDetailSerializer(serializers.ModelSerializer):
    products_count = serializers.IntegerField(source='products_count_annotated', read_only=True)
    subcategories = SubcategorySerializer(many=True, read_only=True)
    parent_name = serializers.CharField(source='parent.name', read_only=True)
    full_path = serializers.CharField(source='get_full_path', read_only=True)
    is_parent = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Category
        fields = '__all__'
        read_only_fields = (
            'id',
            'slug',
            'products_count',
            'parent_name',
            'full_path',
            'is_parent',
            'created_at',
            'updated_at'
        )

class CategoryCreateUpdateSerializer(serializers.ModelSerializer):

    class Meta:
        model = Category
        fields = '__all__'
    
    def validate_parent(self, value):
        if value:
            if self.instance and value.id == self.instance.id:
                raise serializers.ValidationError('Uma categoria não pode ser pai de si mesma.')
            
            if self.instance and value.parent == self.instance:
                raise serializers.ValidationError('Ciclo de categorias detectado.')
        
        return value
    
    def validate_name(self, value):
        queryset = Category.objects.filter(name__iexact=value)
        
        if self.instance:
            queryset = queryset.exclude(id=self.instance.id)
        
        if queryset.exists():
            raise serializers.ValidationError('Já existe uma categoria com este nome.')   
        
        return value
