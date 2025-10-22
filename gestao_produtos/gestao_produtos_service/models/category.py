from django.db import models
from django.utils.text import slugify


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name='Nome')
    slug = models.SlugField(max_length=120, unique=True, blank=True, verbose_name='Slug')
    description = models.TextField(blank=True,verbose_name='Descrição')

    parent = models.ForeignKey('self',on_delete=models.CASCADE,null=True,
        blank=True, related_name='subcategories', verbose_name='Categoria Pai'
    )
    
    image = models.ImageField(upload_to='categories/', null=True, blank=True,verbose_name='Imagem')
    is_active = models.BooleanField(default=True, verbose_name='Ativo')
    order = models.IntegerField(default=0, verbose_name='Ordem de Exibição')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    updated_at = models.DateTimeField(auto_now=True,verbose_name='Atualizado em')
    
    class Meta:
        db_table = 'categories'
        verbose_name = 'Categoria'
        verbose_name_plural = 'Categorias'
        ordering = ['order', 'name']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        if self.parent:
            return f"{self.parent.name} > {self.name}"
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def get_full_path(self):
        if self.parent:
            return f"{self.parent.get_full_path()} > {self.name}"
        return self.name
    
    @property
    def is_parent(self):
        return self.subcategories.exists()
    
    @property
    def products_count(self):
        return self.products.filter(is_active=True).count()
