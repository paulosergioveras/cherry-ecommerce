from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
import os
import requests


class RecomendacaoViewSet(viewsets.ViewSet):
    permission_classes = [AllowAny]
    
    @action(detail=False, methods=['get'])
    def get_recomendation(self, request=None):
        product_url = os.getenv('PRODUCT_SERVICE_URL', 'http://gestao-produtos-service:8002')

        headers = {'Content-Type': 'application/json'}
        print(request.headers)
        if request is not None:
            for h in [
                'X-Forwarded-From-Gateway', 'X-User-ID', 'X-User-Email', 'X-User-Nome',
                'X-User-Is-Admin', 'X-User-Is-Staff', 'X-User-CPF', 'X-User-Role', 'Authorization'
            ]:
                val = request.headers.get(h)
                if val:
                    headers[h] = val

        try:
            response = requests.get(
                f'{product_url}/api/v1/produtos/featured/',
                timeout=5,
                headers=headers if headers else None
            )

            if response.status_code == 200:
                return Response({'produto recomendado':response}, status=status.HTTP_200_OK)
            else:
                return None
        except requests.RequestException as e:
            return Response(e)
        
