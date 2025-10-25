from rest_framework import serializers
from ..models import Notification, NotificationTemplate, NotificationPreference




class NotificationListSerializer(serializers.ModelSerializer):
    notification_type_display = serializers.CharField(
        source='get_notification_type_display',
        read_only=True
    )
    category_display = serializers.CharField(
        source='get_category_display',
        read_only=True
    )
    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True
    )
    is_read = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Notification
        fields = (
            'id',
            'notification_type',
            'notification_type_display',
            'category',
            'category_display',
            'status',
            'status_display',
            'title',
            'message',
            'is_read',
            'created_at',
            'read_at',
        )
        read_only_fields = ('id', 'created_at', 'read_at')

class NotificationDetailSerializer(serializers.ModelSerializer):
    notification_type_display = serializers.CharField(
        source='get_notification_type_display',
        read_only=True
    )
    category_display = serializers.CharField(
        source='get_category_display',
        read_only=True
    )
    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True
    )
    is_sent = serializers.BooleanField(read_only=True)
    is_read = serializers.BooleanField(read_only=True)
    is_failed = serializers.BooleanField(read_only=True)
    can_retry = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Notification
        fields = (
            'id',
            'user_id',
            'user_email',
            'notification_type',
            'notification_type_display',
            'category',
            'category_display',
            'title',
            'message',
            'html_content',
            'data',
            'action_url',
            'status',
            'status_display',
            'attempts',
            'error_message',
            'is_sent',
            'is_read',
            'is_failed',
            'can_retry',
            'created_at',
            'sent_at',
            'read_at',
        )
        read_only_fields = (
            'id',
            'attempts',
            'error_message',
            'created_at',
            'sent_at',
            'read_at',
        )

class NotificationCreateSerializer(serializers.Serializer):
    user_id = serializers.IntegerField(required=True)
    notification_type = serializers.ChoiceField(
        choices=['email', 'sms', 'push', 'in_app'],
        required=True
    )
    category = serializers.ChoiceField(
        choices=['account', 'order', 'payment', 'promotion', 'system'],
        required=True
    )
    title = serializers.CharField(max_length=255, required=True)
    message = serializers.CharField(required=True)
    html_content = serializers.CharField(required=False, allow_blank=True)
    data = serializers.JSONField(required=False, default=dict)
    action_url = serializers.URLField(required=False, allow_blank=True)


class NotificationSendFromTemplateSerializer(serializers.Serializer):
    user_id = serializers.IntegerField(required=True)
    template_name = serializers.CharField(required=True)
    context = serializers.JSONField(required=False, default=dict)
    data = serializers.JSONField(required=False, default=dict)


class NotificationTemplateSerializer(serializers.ModelSerializer):
    notification_type_display = serializers.CharField(
        source='get_notification_type_display',
        read_only=True
    )
    category_display = serializers.CharField(
        source='get_category_display',
        read_only=True
    )
    
    class Meta:
        model = NotificationTemplate
        fields = (
            'id',
            'name',
            'notification_type',
            'notification_type_display',
            'category',
            'category_display',
            'subject',
            'body',
            'html_body',
            'is_active',
            'created_at',
            'updated_at',
        )
        read_only_fields = ('id', 'created_at', 'updated_at')

class NotificationPreferenceSerializer(serializers.ModelSerializer):

    class Meta:
        model = NotificationPreference
        fields = (
            'id',
            'user_id',
            'email_account',
            'email_order',
            'email_payment',
            'email_promotion',
            'sms_order',
            'sms_payment',
            'push_order',
            'push_payment',
            'push_promotion',
            'in_app_all',
            'created_at',
            'updated_at',
        )
        read_only_fields = ('id', 'user_id', 'created_at', 'updated_at')

class MarkAsReadSerializer(serializers.Serializer):
    notification_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=False,
        allow_empty=True
    )
    mark_all = serializers.BooleanField(required=False, default=False)
