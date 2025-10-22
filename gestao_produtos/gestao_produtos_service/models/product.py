from django.db import models
from django.core.validators import MinValueValidator
from django.utils.text import slugify
from decimal import Decimal


class Product(models.Model):
    name = models.CharField(max_length=200, verbose_name='Nome')
    slug = models.SlugField(max_length=220, unique=True, blank=True, verbose_name='Slug')
    description = models.TextField(verbose_name='Descrição')
    category = models.ForeignKey('Category', on_delete=models.PROTECT, related_name='products', verbose_name='Categoria')

    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name='Preço'
    )

    original_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name='Preço Original',
        help_text='Preço antes do desconto'
    )

    stock = models.IntegerField(default=0, validators=[MinValueValidator(0)], verbose_name='Estoque')
    sku = models.CharField(max_length=50, unique=True, verbose_name='SKU', help_text='Código único do produto')
    is_active = models.BooleanField(default=True, verbose_name='Ativo')
    is_featured = models.BooleanField(default=False, verbose_name='Destaque', help_text='Produto em destaque na home')
    views_count = models.IntegerField(default=0, verbose_name='Visualizações')
    sales_count = models.IntegerField(default=0, verbose_name='Vendas')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Atualizado em')
    
    class Meta:
        db_table = 'products'
        verbose_name = 'Produto'
        verbose_name_plural = 'Produtos'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['sku']),
            models.Index(fields=['category']),
            models.Index(fields=['is_active']),
            models.Index(fields=['is_featured']),
            models.Index(fields=['price']),
        ]
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            
            while Product.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            
            self.slug = slug
        
        super().save(*args, **kwargs)
    
    @property
    def is_in_stock(self):
        return self.stock > 0
    
    @property
    def has_discount(self):
        return self.original_price and self.original_price > self.price
    
    @property
    def discount_percentage(self):
        if not self.has_discount:
            return 0
        
        discount = ((self.original_price - self.price) / self.original_price) * 100
        return round(discount, 2)
    
    @property
    def main_image(self):
        return self.images.filter(is_main=True).first()
    
    def increment_views(self):
        self.views_count += 1
        self.save(update_fields=['views_count'])
    
    def increment_sales(self, quantity=1):
        self.sales_count += quantity
        self.save(update_fields=['sales_count'])
    
    def decrease_stock(self, quantity):
        if quantity > self.stock:
            raise ValueError('Quantidade maior que estoque disponível')
        
        self.stock -= quantity
        self.save(update_fields=['stock'])
    
    def increase_stock(self, quantity):
        self.stock += quantity
        self.save(update_fields=['stock'])


class ProductImage(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='images',
        verbose_name='Produto'
    )

    image = models.ImageField(upload_to='products/%Y/%m/', verbose_name='Imagem')
    alt_text = models.CharField(max_length=200, blank=True,verbose_name='Texto Alternativo')
    is_main = models.BooleanField(default=False, verbose_name='Imagem Principal')
    order = models.IntegerField(default=0, verbose_name='Ordem')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    
    class Meta:
        db_table = 'product_images'
        verbose_name = 'Imagem do Produto'
        verbose_name_plural = 'Imagens dos Produtos'
        ordering = ['order', '-is_main', 'created_at']
    
    def __str__(self):
        return f"{self.product.name} - Imagem {self.id}"
    
    def save(self, *args, **kwargs):
        if self.is_main:
            ProductImage.objects.filter(
                product=self.product,
                is_main=True
            ).exclude(id=self.id).update(is_main=False)
        
        if not self.alt_text:
            self.alt_text = self.product.name
        
        super().save(*args, **kwargs)
