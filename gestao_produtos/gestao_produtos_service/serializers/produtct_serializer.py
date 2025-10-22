from rest_framework import serializers
from ..models import Product, ProductImage, Category
from decimal import Decimal




class ProductImageSerializer(serializers.ModelSerializer):

    class Meta:
        model = ProductImage
        fields = (
            'id',
            'image',
            'alt_text',
            'is_main',
            'order',
        )
        read_only_fields = ('id',)

class ProductListSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    main_image_url = serializers.SerializerMethodField()
    has_discount = serializers.BooleanField(read_only=True)
    discount_percentage = serializers.DecimalField(max_digits=5, decimal_places=2, read_only=True)
    
    class Meta:
        model = Product
        fields = '__all__'
        read_only_fields = ('id', 'slug')
    
    def get_main_image_url(self, obj):
        main_image = obj.main_image
        if main_image and main_image.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(main_image.image.url)
            return main_image.image.url
        return None

class ProductDetailSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    category_slug = serializers.CharField(source='category.slug', read_only=True)
    images = ProductImageSerializer(many=True, read_only=True)
    is_in_stock = serializers.BooleanField(read_only=True)
    has_discount = serializers.BooleanField(read_only=True)
    discount_percentage = serializers.DecimalField(max_digits=5, decimal_places=2, read_only=True)
    
    class Meta:
        model = Product
        fields = '__all__'
        read_only_fields = (
            'id',
            'slug',
            'views_count',
            'sales_count',
            'created_at',
            'updated_at',
        )

class ProductCreateUpdateSerializer(serializers.ModelSerializer):
    images_data = serializers.ListField(
        child=serializers.ImageField(),
        write_only=True,
        required=False,
        allow_empty=True
    )
    
    class Meta:
        model = Product
        fields = '__all__'
    
    def validate_category(self, value):
        if not value.is_active:
            raise serializers.ValidationError('Não é possível associar o produto a uma categoria inativa.')
        return value
    
    def validate_sku(self, value):
        queryset = Product.objects.filter(sku=value)
        
        if self.instance:
            queryset = queryset.exclude(id=self.instance.id)
        
        if queryset.exists():
            raise serializers.ValidationError('Já existe um produto com este SKU.')
        
        return value
    
    def validate_price(self, value):
        if value <= 0:
            raise serializers.ValidationError('O preço deve ser maior que zero.')
        return value
    
    def validate_stock(self, value):
        if value < 0:
            raise serializers.ValidationError('O estoque não pode ser negativo.')
        return value
    
    def validate(self, attrs):
        original_price = attrs.get('original_price')
        price = attrs.get('price')
        
        if original_price and price:
            if original_price <= price:
                raise serializers.ValidationError({
                    'original_price': 'O preço original deve ser maior que o preço de venda.'
                })
        
        return attrs
    
    def create(self, validated_data):
        images_data = validated_data.pop('images_data', [])
        product = Product.objects.create(**validated_data)
        
        for index, image in enumerate(images_data):
            ProductImage.objects.create(
                product=product,
                image=image,
                is_main=(index == 0),
                order=index
            )
        
        return product
    
    def update(self, instance, validated_data):
        images_data = validated_data.pop('images_data', None)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        if images_data is not None:
            instance.images.all().delete()
            
            for index, image in enumerate(images_data):
                ProductImage.objects.create(
                    product=instance,
                    image=image,
                    is_main=(index == 0),
                    order=index
                )
        
        return instance

class ProductStockUpdateSerializer(serializers.Serializer):
    quantity = serializers.IntegerField(required=True)
    operation = serializers.ChoiceField(choices=['add', 'remove'], required=True)
    
    def validate_quantity(self, value):
        if value <= 0:
            raise serializers.ValidationError('A quantidade deve ser maior que zero.')
        return value
