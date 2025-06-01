from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q, Count
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend

from .models import Notification, NotificationTemplate, NotificationPreference, PushToken
from .serializers import (
    NotificationSerializer, NotificationTemplateSerializer, NotificationPreferenceSerializer,
    PushTokenSerializer, NotificationCreateSerializer, NotificationSummarySerializer,
    BulkMarkReadSerializer
)
from users.models import CustomUser
from drf_spectacular.utils import extend_schema, extend_schema_view


class NotificationPermission(permissions.BasePermission):
    """
    Custom permission for notifications:
    - Users can only see their own notifications
    - Admins can see all notifications
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        if request.user.is_staff:
            return True
        return obj.recipient == request.user


@extend_schema_view(
    list=extend_schema(summary="List notifications", description="List user's notifications with filtering"),
    retrieve=extend_schema(summary="Get notification", description="Get a specific notification"),
    update=extend_schema(summary="Update notification", description="Update notification (mark as read)"),
    partial_update=extend_schema(summary="Partial update notification", description="Partially update notification"),
)
class NotificationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing user notifications
    """
    serializer_class = NotificationSerializer
    permission_classes = [NotificationPermission]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['is_read', 'priority', 'template__type']
    ordering_fields = ['created_at', 'priority']
    ordering = ['-created_at']
    http_method_names = ['get', 'patch', 'head', 'options']  # Only allow GET and PATCH
    
    def get_queryset(self):
        user = self.request.user
        
        if user.is_staff:
            return Notification.objects.all().select_related('recipient', 'template', 'related_order', 'related_restaurant')
        
        return Notification.objects.filter(recipient=user).select_related('template', 'related_order', 'related_restaurant')
    
    @extend_schema(
        summary="Get notification summary",
        description="Get summary of notification counts and recent notifications"
    )
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """
        Get notification summary for the current user
        """
        user = request.user
        
        notifications_qs = Notification.objects.filter(recipient=user)
        
        total_count = notifications_qs.count()
        unread_count = notifications_qs.filter(is_read=False).count()
        high_priority_unread = notifications_qs.filter(
            is_read=False,
            priority__in=['HIGH', 'URGENT']
        ).count()
        
        recent_notifications = notifications_qs.select_related(
            'template', 'related_order', 'related_restaurant'
        )[:5]
        
        summary_data = {
            'total_notifications': total_count,
            'unread_count': unread_count,
            'high_priority_unread': high_priority_unread,
            'recent_notifications': recent_notifications
        }
        
        serializer = NotificationSummarySerializer(summary_data)
        return Response(serializer.data)
    
    @extend_schema(
        summary="Mark all notifications as read",
        description="Mark all user's notifications as read"
    )
    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        """
        Mark all notifications as read for the current user
        """
        user = request.user
        
        updated_count = Notification.objects.filter(
            recipient=user,
            is_read=False
        ).update(
            is_read=True,
            read_at=timezone.now()
        )
        
        return Response({
            'message': f'Marked {updated_count} notifications as read',
            'updated_count': updated_count
        })
    
    @extend_schema(
        summary="Bulk mark notifications as read",
        description="Mark specific notifications as read"
    )
    @action(detail=False, methods=['post'])
    def bulk_mark_read(self, request):
        """
        Mark specific notifications as read
        """
        serializer = BulkMarkReadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        notification_ids = serializer.validated_data.get('notification_ids', [])
        user = request.user
        
        if notification_ids:
            # Mark specific notifications as read
            updated_count = Notification.objects.filter(
                recipient=user,
                id__in=notification_ids,
                is_read=False
            ).update(
                is_read=True,
                read_at=timezone.now()
            )
        else:
            # Mark all as read if no specific IDs provided
            updated_count = Notification.objects.filter(
                recipient=user,
                is_read=False
            ).update(
                is_read=True,
                read_at=timezone.now()
            )
        
        return Response({
            'message': f'Marked {updated_count} notifications as read',
            'updated_count': updated_count
        })
    
    @extend_schema(
        summary="Get unread notifications",
        description="Get only unread notifications for the current user"
    )
    @action(detail=False, methods=['get'])
    def unread(self, request):
        """
        Get only unread notifications
        """
        user = request.user
        
        unread_notifications = Notification.objects.filter(
            recipient=user,
            is_read=False
        ).select_related('template', 'related_order', 'related_restaurant').order_by('-created_at')
        
        page = self.paginate_queryset(unread_notifications)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(unread_notifications, many=True)
        return Response(serializer.data)
    
    def partial_update(self, request, *args, **kwargs):
        """
        Override partial_update to handle marking as read
        """
        instance = self.get_object()
        
        # If marking as read, also set read_at timestamp
        if request.data.get('is_read') and not instance.is_read:
            request.data['read_at'] = timezone.now()
        
        return super().partial_update(request, *args, **kwargs)


@extend_schema_view(
    list=extend_schema(summary="List notification templates", description="List all notification templates"),
    retrieve=extend_schema(summary="Get notification template", description="Get a specific notification template"),
)
class NotificationTemplateViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for notification templates (read-only)
    """
    queryset = NotificationTemplate.objects.all()
    serializer_class = NotificationTemplateSerializer
    permission_classes = [permissions.IsAuthenticated]


@extend_schema_view(
    retrieve=extend_schema(summary="Get notification preferences", description="Get user's notification preferences"),
    update=extend_schema(summary="Update notification preferences", description="Update user's notification preferences"),
    partial_update=extend_schema(summary="Partial update preferences", description="Partially update notification preferences"),
)
class NotificationPreferenceViewSet(viewsets.ModelViewSet):
    """
    ViewSet for user notification preferences
    """
    serializer_class = NotificationPreferenceSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ['get', 'put', 'patch', 'head', 'options']  # No POST or DELETE
    
    def get_queryset(self):
        return NotificationPreference.objects.filter(user=self.request.user)
    
    def get_object(self):
        """
        Get or create notification preferences for the current user
        """
        user = self.request.user
        preferences, created = NotificationPreference.objects.get_or_create(user=user)
        return preferences


@extend_schema_view(
    list=extend_schema(summary="List push tokens", description="List user's push notification tokens"),
    create=extend_schema(summary="Register push token", description="Register a new push notification token"),
    destroy=extend_schema(summary="Unregister push token", description="Remove a push notification token"),
)
class PushTokenViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing push notification tokens
    """
    serializer_class = PushTokenSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ['get', 'post', 'delete', 'head', 'options']
    
    def get_queryset(self):
        return PushToken.objects.filter(user=self.request.user)


class AdminNotificationViewSet(viewsets.ViewSet):
    """
    Admin-only viewset for creating and managing notifications
    """
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]
    
    @extend_schema(
        summary="Create notification",
        description="Create and send notifications to users (Admin only)"
    )
    @action(detail=False, methods=['post'])
    def create_notification(self, request):
        """
        Create and send notifications to specified users
        """
        serializer = NotificationCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        data = serializer.validated_data
        
        # Determine recipients
        recipients = []
        
        if data.get('recipient_ids'):
            recipients.extend(
                CustomUser.objects.filter(id__in=data['recipient_ids'])
            )
        
        if data.get('recipient_roles'):
            recipients.extend(
                CustomUser.objects.filter(role__in=data['recipient_roles'])
            )
        
        # Remove duplicates
        recipients = list(set(recipients))
        
        if not recipients:
            return Response(
                {"error": "No valid recipients found"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get template if specified
        template = None
        if data.get('template_type'):
            try:
                template = NotificationTemplate.objects.get(type=data['template_type'])
            except NotificationTemplate.DoesNotExist:
                pass
        
        # Create notifications
        notifications_created = []
        for recipient in recipients:
            notification = Notification.objects.create(
                recipient=recipient,
                template=template,
                title=data['title'],
                message=data['message'],
                priority=data['priority'],
                action_url=data.get('action_url'),
                action_text=data.get('action_text'),
                metadata=data.get('metadata', {}),
                related_order_id=data.get('related_order_id'),
                related_restaurant_id=data.get('related_restaurant_id'),
            )
            notifications_created.append(notification)
        
        return Response({
            'message': f'Created {len(notifications_created)} notifications',
            'notification_count': len(notifications_created),
            'recipient_count': len(recipients)
        }, status=status.HTTP_201_CREATED)
    
    @extend_schema(
        summary="Get notification statistics",
        description="Get platform-wide notification statistics (Admin only)"
    )
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """
        Get notification statistics for admin dashboard
        """
        from datetime import timedelta
        
        end_date = timezone.now()
        start_date = end_date - timedelta(days=30)
        
        # Get statistics
        total_notifications = Notification.objects.count()
        recent_notifications = Notification.objects.filter(
            created_at__gte=start_date
        ).count()
        
        unread_count = Notification.objects.filter(is_read=False).count()
        
        # Notifications by type
        by_type = Notification.objects.filter(
            created_at__gte=start_date
        ).values('template__type').annotate(
            count=Count('id')
        ).order_by('-count')
        
        # Notifications by priority
        by_priority = Notification.objects.filter(
            created_at__gte=start_date
        ).values('priority').annotate(
            count=Count('id')
        ).order_by('-count')
        
        return Response({
            'total_notifications': total_notifications,
            'recent_notifications': recent_notifications,
            'unread_notifications': unread_count,
            'notifications_by_type': list(by_type),
            'notifications_by_priority': list(by_priority),
            'period_days': 30
        })
