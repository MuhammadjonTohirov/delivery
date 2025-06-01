from rest_framework import serializers
from .models import Notification, NotificationTemplate, NotificationPreference, PushToken, NotificationLog


class NotificationTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationTemplate
        fields = '__all__'


class NotificationSerializer(serializers.ModelSerializer):
    recipient_name = serializers.CharField(source='recipient.full_name', read_only=True)
    template_type = serializers.CharField(source='template.type', read_only=True)
    related_order_id = serializers.UUIDField(source='related_order.id', read_only=True)
    related_restaurant_name = serializers.CharField(source='related_restaurant.name', read_only=True)
    time_ago = serializers.SerializerMethodField()
    
    class Meta:
        model = Notification
        fields = [
            'id', 'recipient', 'recipient_name', 'template', 'template_type',
            'title', 'message', 'priority', 'related_order', 'related_order_id',
            'related_restaurant', 'related_restaurant_name', 'is_read', 'read_at',
            'action_url', 'action_text', 'metadata', 'time_ago', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'recipient', 'created_at', 'updated_at']
    
    def get_time_ago(self, obj):
        """
        Get human-readable time since notification was created
        """
        from django.utils import timezone
        from datetime import timedelta
        
        now = timezone.now()
        diff = now - obj.created_at
        
        if diff.days > 0:
            return f"{diff.days} day{'s' if diff.days > 1 else ''} ago"
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f"{hours} hour{'s' if hours > 1 else ''} ago"
        elif diff.seconds > 60:
            minutes = diff.seconds // 60
            return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
        else:
            return "Just now"


class NotificationPreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationPreference
        fields = '__all__'
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']


class PushTokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = PushToken
        fields = ['id', 'token', 'device_type', 'device_id', 'is_active', 'last_used', 'created_at']
        read_only_fields = ['id', 'user', 'last_used', 'created_at']
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class NotificationLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationLog
        fields = '__all__'


class NotificationCreateSerializer(serializers.Serializer):
    """
    Serializer for creating notifications programmatically
    """
    recipient_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=False,
        help_text="List of user IDs to send notification to"
    )
    recipient_roles = serializers.ListField(
        child=serializers.ChoiceField(choices=[
            ('CUSTOMER', 'Customer'),
            ('DRIVER', 'Driver'),
            ('RESTAURANT', 'Restaurant'),
            ('ADMIN', 'Admin'),
        ]),
        required=False,
        help_text="Send to all users with these roles"
    )
    template_type = serializers.CharField(required=False)
    title = serializers.CharField(max_length=200)
    message = serializers.CharField()
    priority = serializers.ChoiceField(
        choices=Notification.PRIORITY_CHOICES,
        default='MEDIUM'
    )
    action_url = serializers.URLField(required=False)
    action_text = serializers.CharField(max_length=50, required=False)
    metadata = serializers.JSONField(required=False, default=dict)
    related_order_id = serializers.UUIDField(required=False)
    related_restaurant_id = serializers.UUIDField(required=False)
    
    def validate(self, data):
        if not data.get('recipient_ids') and not data.get('recipient_roles'):
            raise serializers.ValidationError(
                "Either recipient_ids or recipient_roles must be provided"
            )
        return data


class NotificationSummarySerializer(serializers.Serializer):
    """
    Serializer for notification summary/counts
    """
    total_notifications = serializers.IntegerField()
    unread_count = serializers.IntegerField()
    high_priority_unread = serializers.IntegerField()
    recent_notifications = NotificationSerializer(many=True)


class BulkMarkReadSerializer(serializers.Serializer):
    """
    Serializer for bulk marking notifications as read
    """
    notification_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=False,
        help_text="List of notification IDs to mark as read. If empty, marks all as read."
    )
