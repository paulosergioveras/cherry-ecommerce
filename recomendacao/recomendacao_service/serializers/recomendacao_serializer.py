from rest_framework import serializers
from ..models import VisualizacaoProduto, InteracaoProduto, AvaliacaoProduto, RecomendacaoGerada




class VisualizacaoProdutoSerializer(serializers.ModelSerializer):

    class Meta:
        model = VisualizacaoProduto
        fields = ['id', 'usuario_id', 'produto_id', 'visualizado_em']
        read_only_fields = ['id', 'visualizado_em']

class InteracaoProdutoSerializer(serializers.ModelSerializer):

    class Meta:
        model = InteracaoProduto
        fields = ['id', 'usuario_id', 'produto_id', 'tipo', 'peso', 'criado_em']
        read_only_fields = ['id', 'criado_em']
    
    def validate_peso(self, value):
        if value < 1:
            raise serializers.ValidationError("Peso deve ser no mínimo 1")
        return value

class AvaliacaoProdutoSerializer(serializers.ModelSerializer):

    class Meta:
        model = AvaliacaoProduto
        fields = ['id', 'usuario_id', 'produto_id', 'nota', 'comentario', 'criado_em', 'atualizado_em']
        read_only_fields = ['id', 'criado_em', 'atualizado_em']
    
    def validate_nota(self, value):
        if not 1 <= value <= 5:
            raise serializers.ValidationError("Nota deve estar entre 1 e 5")
        return value

class RecomendacaoGeradaSerializer(serializers.ModelSerializer):

    class Meta:
        model = RecomendacaoGerada
        fields = ['id', 'usuario_id', 'tipo_recomendacao', 'produtos_ids', 'score', 'gerado_em', 'expira_em']
        read_only_fields = ['id', 'gerado_em']

class RecomendacaoRequestSerializer(serializers.Serializer):
    usuario_id = serializers.IntegerField(required=False, allow_null=True)
    tipo = serializers.ChoiceField(
        choices=['popular', 'similar', 'personalizado', 'categoria', 'carrinho'],
        default='popular'
    )
    produto_id = serializers.IntegerField(required=False, allow_null=True)
    categoria_id = serializers.IntegerField(required=False, allow_null=True)
    limite = serializers.IntegerField(default=10, min_value=1, max_value=50)

class RecomendacaoResponseSerializer(serializers.Serializer):
    produtos = serializers.ListField(
        child=serializers.DictField()
    )
    tipo_recomendacao = serializers.CharField()
    total = serializers.IntegerField()
    gerado_em = serializers.DateTimeField()
