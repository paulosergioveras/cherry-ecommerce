from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

class VisualizacaoProduto(models.Model):
    usuario_id = models.IntegerField()
    produto_id = models.IntegerField()
    visualizado_em = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'visualizacao_produto'
        ordering = ['-visualizado_em']
        indexes = [
            models.Index(fields=['usuario_id', '-visualizado_em']),
            models.Index(fields=['produto_id']),
        ]
    
    def __str__(self):
        return f"Usuario {self.usuario_id} - Produto {self.produto_id}"

class InteracaoProduto(models.Model):
    TIPO_CHOICES = [
        ('VIEW', 'Visualização'),
        ('CART', 'Adição ao Carrinho'),
        ('PURCHASE', 'Compra'),
        ('FAVORITE', 'Favorito'),
    ]
    
    usuario_id = models.IntegerField()
    produto_id = models.IntegerField()
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES)
    peso = models.IntegerField(default=1)
    criado_em = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'interacao_produto'
        ordering = ['-criado_em']
        indexes = [
            models.Index(fields=['usuario_id', 'tipo']),
            models.Index(fields=['produto_id', 'tipo']),
        ]
    
    def __str__(self):
        return f"Usuario {self.usuario_id} - {self.tipo} - Produto {self.produto_id}"


class RecomendacaoGerada(models.Model):
    usuario_id = models.IntegerField(null=True, blank=True)
    tipo_recomendacao = models.CharField(max_length=50)
    produtos_ids = models.JSONField()
    score = models.FloatField(default=0.0)
    gerado_em = models.DateTimeField(auto_now=True)
    expira_em = models.DateTimeField()
    
    class Meta:
        db_table = 'recomendacao_gerada'
        ordering = ['-gerado_em']
        indexes = [
            models.Index(fields=['usuario_id', 'tipo_recomendacao']),
            models.Index(fields=['expira_em']),
        ]
    
    def __str__(self):
        usuario = self.usuario_id or 'Geral'
        return f"{self.tipo_recomendacao} - Usuario {usuario}"

class AvaliacaoProduto(models.Model):
    usuario_id = models.IntegerField()
    produto_id = models.IntegerField()
    nota = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comentario = models.TextField(blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'avaliacao_produto'
        unique_together = ['usuario_id', 'produto_id']
        ordering = ['-criado_em']
        indexes = [
            models.Index(fields=['produto_id', '-nota']),
            models.Index(fields=['usuario_id']),
        ]
    
    def __str__(self):
        return f"Usuario {self.usuario_id} - Produto {self.produto_id} - Nota {self.nota}"
