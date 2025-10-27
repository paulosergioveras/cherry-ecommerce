from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.exceptions import AuthenticationFailed
from django.contrib.auth.models import AnonymousUser




class AuthenticatedAnonymousUser(AnonymousUser):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._is_authenticated = False

    @property
    def is_authenticated(self):
        return self._is_authenticated

    @is_authenticated.setter
    def is_authenticated(self, value):
        self._is_authenticated = value


class GatewayJWTAuthentication(JWTAuthentication):
    def authenticate(self, request):
        if 'X-Forwarded-From-Gateway' in request.headers:
            user_id = request.headers.get('X-User-ID')
            if not user_id:
                raise AuthenticationFailed('User not found', code='user_not_found')

            user = AuthenticatedAnonymousUser()
            user.id = int(user_id)
            user.email = request.headers.get('X-User-Email', '')
            role_val = request.headers.get('X-User-Role', '').lower()
            user.role = role_val
            user.is_admin = role_val in ['admin', 'admin_master']
            user.is_admin_master = role_val == 'admin_master'
            user.is_customer = not (user.is_admin or user.is_admin_master)
            user.cpf = request.headers.get('X-User-CPF', '').lower()
            user.nome = request.headers.get('X-User-Nome', '').lower()
            user.access_token = request.headers.get('Authorization', '').split(' ')[-1]
            user.is_authenticated = True
            
            return (user, None)
        
        return super().authenticate(request)
