from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.http import FileResponse
import requests
import logging

logger = logging.getLogger(__name__)


class MicroserviceRouter(APIView):
    """
    Classe base para roteamento de requisições para microsserviços do Cherry E-commerce
    """
    service_url = None
    service_prefix = ''
    verify_token_url = 'http://gestao-usuarios-service:8001/api/v1/users/verify-token/'

    def _verify_token(self, request):
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            logger.warning("No authorization header provided")
            return None
            
        token = auth_header.split(' ')[-1] if auth_header else None
        
        try:
            response = requests.post(
                self.verify_token_url,
                json={'token': token},
                timeout=3
            )
            
            if response.status_code == 200:
                logger.info("Token verified successfully")
                return response
            else:
                logger.warning(f"Token verification failed with status {response.status_code}")
                return None
                
        except requests.RequestException as e:
            logger.error(f"Error verifying token: {str(e)}")
            return None

    def _is_public_endpoint(self, path, method):
        """
        Define quais endpoints são públicos (não precisam de autenticação)
        """
        if 'register/admin' in path:
            return False

        unauthenticated_paths = [
            # Autenticação e cadastro
            'login',
            'login-guest',
            'admin-login',
            # generic 'register' removed to avoid matching admin register
            'cadastro',
            'auth',
            'refresh',
            ('usuarios', 'POST'),  # Cadastro de usuário
            'register',
            
            # Produtos (leitura pública)
            ('produtos', 'GET'),
            ('categorias', 'GET'),
            ('buscar', 'GET'),
            
            # Recomendações (leitura pública)
            
            
            # Health check
            'health',
        ]
        
        requires_auth = True
        for item in unauthenticated_paths:
            if isinstance(item, tuple):
                # Tupla (endpoint, método)
                if item[0] in path and item[1] == method:
                    requires_auth = False
                    break
            else:
                # String simples
                if item in path:
                    requires_auth = False
                    break
        
        return not requires_auth

    def _proxy_request(self, request, path=''):
        """
        Faz o proxy da requisição para o microsserviço correspondente
        """
        user_info = None 
        method = request.method
        
        # Verificar se o endpoint requer autenticação
        is_public = self._is_public_endpoint(path, method)
        
        # Se não é público, verificar token
        if not is_public:
            auth_response = self._verify_token(request)
            if not auth_response:
                return Response(
                    {'error': 'Token inválido ou expirado'},
                    status=status.HTTP_401_UNAUTHORIZED
                )
            
            try:
                user_info = auth_response.json()
                logger.info(f"User authenticated: {user_info.get('user_id', 'unknown')}")
            except Exception as e:
                logger.error(f"Error parsing auth response: {e}")
                return Response(
                    {'error': 'Erro na autenticação'},
                    status=status.HTTP_401_UNAUTHORIZED
                )
        
        # Construir URL completa
        try:
            base_url = self.service_url.rstrip('/')
            prefix = self.service_prefix.strip('/')
            path = path.strip('/')
            
            # Montar URL: base_url/prefix/path/
            url_parts = [part for part in [base_url, prefix, path] if part]
            full_url = '/'.join(url_parts)
            
            # Adicionar / no final se necessário
            if not full_url.endswith('/') and '?' not in full_url:
                full_url += '/'
            
            logger.info(f"Proxying {method} request to: {full_url}")
            
            # Preparar headers
            headers = {
                'Content-Type': request.headers.get('Content-Type', 'application/json'),
                'X-Forwarded-From-Gateway': 'true',
                'X-Original-Path': request.path,
                'X-Original-Method': method,
            }
            
            # Se usuário autenticado, adicionar informações do usuário nos headers
            if user_info:
                headers.update({
                    'Authorization': request.headers.get('Authorization', ''),
                    'X-User-ID': str(user_info.get('user_id', '')),
                    'X-User-Email': user_info.get('user_email', ''),
                    'X-User-Nome': user_info.get('nome', ''),
                    'X-User-Is-Admin': 'true' if user_info.get('is_admin', False) else 'false',
                    'X-User-Is-Staff': 'true' if user_info.get('is_staff', False) else 'false',
                    'X-User-CPF': user_info.get('cpf', ''),
                    'X-User-Role': user_info.get('role', '')
                })
            
            logger.debug(f"Request headers: {headers}")
            
            # Copiar query params
            params = request.GET.dict() if request.GET else None
            
            # Fazer requisição ao microsserviço
            response = requests.request(
                method=method,
                url=full_url,
                headers=headers,
                data=request.body if request.body else None,
                params=params,
                timeout=30,
                stream=True
            )
            
            logger.info(
                f"Response from service: status={response.status_code}, "
                f"content-type={response.headers.get('Content-Type')}"
            )
            
            # Verificar se é resposta de arquivo (download)
            content_type = response.headers.get('Content-Type', '')
            if 'application/json' not in content_type and 'text/' not in content_type:
                # Retornar arquivo
                proxy_response = FileResponse(
                    response.raw,
                    content_type=content_type,
                    status=response.status_code
                )
                
                # Copiar headers relevantes
                if 'Content-Disposition' in response.headers:
                    proxy_response['Content-Disposition'] = response.headers['Content-Disposition']
                if 'Content-Length' in response.headers:
                    proxy_response['Content-Length'] = response.headers['Content-Length']
                
                return proxy_response
            
            # Criar resposta proxy
            proxy_response = Response(
                content_type=content_type,
                status=response.status_code
            )
            
            # Adicionar dados JSON se houver
            try:
                proxy_response.data = response.json() if response.content else {}
            except Exception as e:
                logger.warning(f"Error parsing JSON response: {e}")
                proxy_response.data = {'detail': response.text if response.text else 'No content'}
            
            return proxy_response
            
        except requests.exceptions.Timeout:
            logger.error(f"Timeout connecting to {self.service_url}")
            return Response(
                {'error': 'Timeout ao conectar com o serviço', 'service': self.service_url},
                status=status.HTTP_504_GATEWAY_TIMEOUT
            )
        
        except requests.exceptions.ConnectionError:
            logger.error(f"Connection error to {self.service_url}")
            return Response(
                {'error': 'Serviço indisponível', 'service': self.service_url},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        
        except Exception as e:
            logger.exception(f"Unexpected error proxying request: {e}")
            return Response(
                {'error': 'Erro interno no gateway', 'detail': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            
    def get(self, request, path=''):
        """GET request"""
        return self._proxy_request(request, path)
    
    def post(self, request, path=''):
        """POST request"""
        return self._proxy_request(request, path)
    
    def put(self, request, path=''):
        """PUT request"""
        return self._proxy_request(request, path)
    
    def patch(self, request, path=''):
        """PATCH request"""
        return self._proxy_request(request, path)
    
    def delete(self, request, path=''):
        """DELETE request"""
        return self._proxy_request(request, path)
