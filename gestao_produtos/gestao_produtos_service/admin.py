from django.contrib import admin
from django.utils.html import format_html
from .models import Category, Product, ProductImage




class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ('image', 'alt_text', 'is_main', 'order')
    readonly_fields = ('image_preview',)
    
    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-height: 100px;"/>',
                obj.image.url
            )
        return '-'
    image_preview.short_description = 'Preview'


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'parent',
        'products_count_display',
        'is_active',
        'order',
        'created_at'
    )
    list_filter = ('is_active', 'parent', 'created_at')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    ordering = ('order', 'name')
    readonly_fields = ('created_at', 'updated_at', 'image_preview')
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('name', 'slug', 'description', 'parent')
        }),
        ('Imagem', {
            'fields': ('image', 'image_preview')
        }),
        ('Configurações', {
            'fields': ('is_active', 'order')
        }),
        ('Datas', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def products_count_display(self, obj):
        count = obj.products.filter(is_active=True).count()
        return f"{count} produtos"
    products_count_display.short_description = 'Produtos'
    
    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-height: 200px;"/>',
                obj.image.url
            )
        return '-'
    image_preview.short_description = 'Preview'

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        'image_preview_small',
        'name',
        'category',
        'price_display',
        'stock',
        'is_active',
        'is_featured',
        'sales_count',
        'created_at'
    )
    list_filter = (
        'is_active',
        'is_featured',
        'category',
        'created_at'
    )
    search_fields = ('name', 'description', 'sku')
    readonly_fields = (
        'slug',
        'views_count',
        'sales_count',
        'created_at',
        'updated_at',
        'is_in_stock',
        'has_discount',
        'discount_percentage'
    )
    ordering = ('-created_at',)
    inlines = [ProductImageInline]
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': (
                'name',
                'slug',
                'description',
                'category',
                'sku'
            )
        }),
        ('Preço e Estoque', {
            'fields': (
                'price',
                'original_price',
                'stock'
            )
        }),
        ('Status', {
            'fields': (
                'is_active',
                'is_featured',
                'is_in_stock',
                'has_discount',
                'discount_percentage'
            )
        }),
        ('Estatísticas', {
            'fields': (
                'views_count',
                'sales_count'
            ),
            'classes': ('collapse',)
        }),
        ('Datas', {
            'fields': (
                'created_at',
                'updated_at'
            ),
            'classes': ('collapse',)
        }),
    )
    
    def image_preview_small(self, obj):
        main_image = obj.main_image
        if main_image and main_image.image:
            return format_html(
                '<img src="{}" style="max-height: 50px; max-width: 50px;"/>',
                main_image.image.url
            )
        return '-'
    image_preview_small.short_description = 'Imagem'
    
    def price_display(self, obj):
        if obj.has_discount:
            return format_html(
                '<span style="color: green;">R$ {:.2f}</span> '
                '<s style="color: gray;">R$ {:.2f}</s> '
                '<span style="color: red;">(-{}%)</span>',
                obj.price,
                obj.original_price,
                obj.discount_percentage
            )
        return format_
