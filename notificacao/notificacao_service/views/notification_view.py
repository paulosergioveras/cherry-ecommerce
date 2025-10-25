from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import Q
import requests
import os

from ..models import (
    Notification,
    NotificationTemplate,
    NotificationPreference,
    PENDING,
    SENDING,
    SENT,
    FAILED,
    READ,
)
from ..serializers import (
    NotificationListSerializer,
    NotificationDetailSerializer,
    NotificationCreateSerializer,
    NotificationSendFromTemplateSerializer,
    NotificationTemplateSerializer,
    NotificationPreferenceSerializer,
    MarkAsReadSerializer,
)




class IsAuthenticatedOrAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        if hasattr(request.user, 'is_admin') and (request.user.is_admin or request.user.is_admin_master):
            return True
        
        return obj.user_id == request.user.id

class NotificationViewSet(viewsets.ModelViewSet):
    queryset = Notification.objects.all()
    permission_classes = [IsAuthenticatedOrAdmin]
    
    def get_serializer_class(self):
        if self.action == 'list':
            return NotificationListSerializer
        elif self.action == 'create':
            return NotificationCreateSerializer
        return NotificationDetailSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        
        if hasattr(user, 'is_admin') and (user.is_admin or user.is_admin_master):
            return queryset
        
        return queryset.filter(user_id=user.id)
    
    def list(self, request):
        queryset = self.get_queryset()
        notification_type = request.query_params.get('type')
        category = request.query_params.get('category')
        status_filter = request.query_params.get('status')
        unread_only = request.query_params.get('unread_only')
        
        if notification_type:
            queryset = queryset.filter(notification_type=notification_type)
        
        if category:
            queryset = queryset.filter(category=category)
        
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        if unread_only == 'true':
            queryset = queryset.exclude(status=READ)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    def create(self, request):
        if not (hasattr(request.user, 'is_admin') and 
                (request.user.is_admin or request.user.is_admin_master)):
            return Response(
                {'error': 'Apenas administradores podem criar notificações.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = NotificationCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user_data = self._get_user_data(serializer.validated_data['user_id'])
        
        if not user_data:
            return Response({
                'error': 'Usuário não encontrado.'
            }, status=status.HTTP_404_NOT_FOUND)
        
        if not self._check_preferences(
            serializer.validated_data['user_id'],
            serializer.validated_data['notification_type'],
            serializer.validated_data['category']
        ):
            return Response({
                'message': 'Usuário optou por não receber este tipo de notificação.'
            }, status=status.HTTP_200_OK)
        
        notification = Notification.objects.create(
            user_id=user_data['id'],
            user_email=user_data['email'],
            user_phone=user_data.get('phone', ''),
            notification_type=serializer.validated_data['notification_type'],
            category=serializer.validated_data['category'],
            title=serializer.validated_data['title'],
            message=serializer.validated_data['message'],
            html_content=serializer.validated_data.get('html_content', ''),
            data=serializer.validated_data.get('data', {}),
            action_url=serializer.validated_data.get('action_url', ''),
        )
        
        self._send_notification(notification)
        
        return Response({
            'message': 'Notificação enviada com sucesso!',
            'notification': NotificationDetailSerializer(notification).data
        }, status=status.HTTP_201_CREATED)
    
    def retrieve(self, request, pk=None):
        notification = self.get_object()
        serializer = self.get_serializer(notification)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def send_from_template(self, request):
        serializer = NotificationSendFromTemplateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user_id = serializer.validated_data['user_id']
        template_name = serializer.validated_data['template_name']
        context = serializer.validated_data.get('context', {})
        data = serializer.validated_data.get('data', {})
        
        try:
            template = NotificationTemplate.objects.get(
                name=template_name,
                is_active=True
            )
        except NotificationTemplate.DoesNotExist:
            return Response({
                'error': 'Template não encontrado.'
            }, status=status.HTTP_404_NOT_FOUND)
        
        user_data = self._get_user_data(user_id)
        
        if not user_data:
            return Response({
                'error': 'Usuário não encontrado.'
            }, status=status.HTTP_404_NOT_FOUND)
        
        if not self._check_preferences(user_id, template.notification_type, template.category):
            return Response({
                'message': 'Usuário optou por não receber este tipo de notificação.'
            }, status=status.HTTP_200_OK)
        
        rendered = template.render(context)
        
        notification = Notification.objects.create(
            user_id=user_data['id'],
            user_email=user_data['email'],
            user_phone=user_data.get('phone', ''),
            notification_type=template.notification_type,
            category=template.category,
            title=rendered['subject'],
            message=rendered['body'],
            html_content=rendered['html_body'],
            data=data,
        )
        
        self._send_notification(notification)
        
        return Response({
            'message': 'Notificação enviada com sucesso!',
            'notification': NotificationDetailSerializer(notification).data
        }, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'])
    def mark_as_read(self, request, pk=None):
        notification = self.get_object()
        
        if notification.status != READ:
            notification.status = READ
            notification.read_at = timezone.now()
            notification.save()
        
        return Response({
            'message': 'Notificação marcada como lida!'
        })
    
    @action(detail=False, methods=['post'])
    def mark_multiple_as_read(self, request):
        serializer = MarkAsReadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        mark_all = serializer.validated_data.get('mark_all', False)
        notification_ids = serializer.validated_data.get('notification_ids', [])
        
        queryset = self.get_queryset().exclude(status=READ)
        
        if mark_all:
            count = queryset.update(
                status=READ,
                read_at=timezone.now()
            )
        elif notification_ids:
            count = queryset.filter(id__in=notification_ids).update(
                status=READ,
                read_at=timezone.now()
            )
        else:
            return Response({
                'error': 'Forneça notification_ids ou mark_all=true'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({
            'message': f'{count} notificação(ões) marcada(s) como lida(s)!'
        })
    
    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        count = self.get_queryset().exclude(status=READ).count()
        
        return Response({
            'unread_count': count
        })
    
    @action(detail=True, methods=['post'])
    def retry(self, request, pk=None):
        if not (hasattr(request.user, 'is_admin') and 
                (request.user.is_admin or request.user.is_admin_master)):
            return Response(
                {'error': 'Apenas administradores podem reenviar notificações.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        notification = self.get_object()
        
        if not notification.can_retry:
            return Response({
                'error': 'Esta notificação não pode ser reenviada.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        self._send_notification(notification)
        
        return Response({
            'message': 'Notificação reenviada!',
            'notification': NotificationDetailSerializer(notification).data
        })
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        if not (hasattr(request.user, 'is_admin') and 
                (request.user.is_admin or request.user.is_admin_master)):
            return Response(
                {'error': 'Apenas administradores podem ver estatísticas.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        queryset = Notification.objects.all()
        
        stats = {
            'total': queryset.count(),
            'by_status': {
                'pending': queryset.filter(status=PENDING).count(),
                'sending': queryset.filter(status=SENDING).count(),
                'sent': queryset.filter(status=SENT).count(),
                'failed': queryset.filter(status=FAILED).count(),
                'read': queryset.filter(status=READ).count(),
            },
            'by_type': {
                'email': queryset.filter(notification_type='email').count(),
                'sms': queryset.filter(notification_type='sms').count(),
                'push': queryset.filter(notification_type='push').count(),
                'in_app': queryset.filter(notification_type='in_app').count(),
            },
            'by_category': {
                'account': queryset.filter(category='account').count(),
                'order': queryset.filter(category='order').count(),
                'payment': queryset.filter(category='payment').count(),
                'promotion': queryset.filter(category='promotion').count(),
                'system': queryset.filter(category='system').count(),
            }
        }
        
        return Response(stats)


    def _get_user_data(self, user_id):
        users_url = os.getenv('USERS_SERVICE_URL', 'http://gestao-usuarios-service:8001')
        
        try:
            response = requests.get(
                f'{users_url}/api/v1/users/{user_id}/',
                timeout=5
            )
            
            if response.status_code == 200:
                return response.json()
        except:
            pass
        
        return None
    
    def _check_preferences(self, user_id, notification_type, category):
        try:
            preferences = NotificationPreference.objects.get(user_id=user_id)
            return preferences.can_receive(notification_type, category)
        except NotificationPreference.DoesNotExist:
            return True
    
    def _send_notification(self, notification):
        notification.status = SENDING
        notification.attempts += 1
        notification.save()
        
        try:
            if notification.notification_type == 'email':
                self._send_email(notification)
            elif notification.notification_type == 'sms':
                self._send_sms(notification)
            elif notification.notification_type == 'push':
                self._send_push(notification)
            elif notification.notification_type == 'in_app':
                self._send_in_app(notification)
            
            notification.status = SENT
            notification.sent_at = timezone.now()
            notification.save()
            
        except Exception as e:
            notification.status = FAILED
            notification.error_message = str(e)
            notification.save()
    
    def _send_email(self, notification):
        print(f"Enviando email para {notification.user_email}")
        print(f"Título: {notification.title}")
        print(f"Mensagem: {notification.message}")
    
    def _send_sms(self, notification):
        print(f"Enviando SMS para {notification.user_phone}")
        print(f"Mensagem: {notification.message}")
    
    def _send_push(self, notification):
        print(f"Enviando push para usuário {notification.user_id}")
        print(f"Título: {notification.title}")
    
    def _send_in_app(self, notification):
        pass

class NotificationPreferenceViewSet(viewsets.ModelViewSet):
    queryset = NotificationPreference.objects.all()
    serializer_class = NotificationPreferenceSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return self.queryset.filter(user_id=self.request.user.id)
    
    @action(detail=False, methods=['get', 'put'])
    def my_preferences(self, request):
        preferences, created = NotificationPreference.objects.get_or_create(
            user_id=request.user.id
        )
        
        if request.method == 'GET':
            serializer = self.get_serializer(preferences)
            return Response(serializer.data)
        
        elif request.method == 'PUT':
            serializer = self.get_serializer(
                preferences,
                data=request.data,
                partial=True
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            
            return Response({
                'message': 'Preferências atualizadas com sucesso!',
                'preferences': serializer.data
            })
