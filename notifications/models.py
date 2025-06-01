from django.db import models
from django.conf import settings
from django.utils import timezone
from core.models import TimeStampedModel
import uuid


class NotificationTemplate(models.Model):
    """
    Template for different types of notifications
    """
    NOTIFICATION_TYPES = (
        ('ORDER_PLACED', 'Order Placed'),
        ('ORDER_CONFIRMED', 'Order Confirmed'),
        ('ORDER_PREPARING', 'Order Being Prepared'),
        ('ORDER_READY', 'Order Ready for Pickup'),
        ('ORDER_PICKED_UP', 'Order Picked Up'),
        ('ORDER_DELIVERED', 'Order Delivered'),
        ('ORDER_CANCELLED', 'Order Cancelled'),
        ('DRIVER_ASSIGNED', 'Driver Assigned'),
        ('DRIVER_NEARBY', 'Driver Nearby'),
        ('PAYMENT_SUCCESSFUL', 'Payment Successful'),
        ('PAYMENT_FAILED', 'Payment Failed'),
        ('REVIEW_REQUEST', 'Review Request'),
        ('PROMOTION_AVAILABLE', 'Promotion Available'),
        ('RESTAURANT_OPENED', 'Restaurant Opened'),
        ('RESTAURANT_CLOSED', 'Restaurant Closed'),
        ('SYSTEM_MAINTENANCE', 'System Maintenance'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    type = models.CharField(max_length=50, choices=NOTIFICATION_TYPES, unique=True)
    title_template = models.CharField(max_length=200)
    message_template = models.TextField()
    
    # Notification settings
    is_active = models.BooleanField(default=True)
    send_push = models.BooleanField(default=True)
    send_email = models.BooleanField(default=False)
    send_sms = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.get_type_display()} Template"


class Notification(TimeStampedModel):
    """
    Individual notification sent to users
    """
    PRIORITY_CHOICES = (
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
        ('URGENT', 'Urgent'),
    )
    
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    template = models.ForeignKey(NotificationTemplate, on_delete=models.SET_NULL, null=True, blank=True)
    
    title = models.CharField(max_length=200)
    message = models.TextField()
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='MEDIUM')
    
    # Related objects
    related_order = models.ForeignKey('orders.Order', on_delete=models.CASCADE, null=True, blank=True)
    related_restaurant = models.ForeignKey('restaurants.Restaurant', on_delete=models.CASCADE, null=True, blank=True)
    
    # Status
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    
    # Delivery status
    sent_push = models.BooleanField(default=False)
    sent_email = models.BooleanField(default=False)
    sent_sms = models.BooleanField(default=False)
    
    # Additional data
    action_url = models.URLField(null=True, blank=True)
    action_text = models.CharField(max_length=50, null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', 'is_read', 'created_at']),
            models.Index(fields=['recipient', 'created_at']),
            models.Index(fields=['template', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.recipient.full_name}"
    
    def mark_as_read(self):
        """
        Mark notification as read
        """
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])


class NotificationPreference(models.Model):
    """
    User preferences for different types of notifications
    """
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notification_preferences')
    
    # Order notifications
    order_updates_push = models.BooleanField(default=True)
    order_updates_email = models.BooleanField(default=True)
    order_updates_sms = models.BooleanField(default=False)
    
    # Promotion notifications
    promotions_push = models.BooleanField(default=True)
    promotions_email = models.BooleanField(default=False)
    promotions_sms = models.BooleanField(default=False)
    
    # System notifications
    system_updates_push = models.BooleanField(default=True)
    system_updates_email = models.BooleanField(default=False)
    
    # Restaurant notifications (for restaurant owners)
    restaurant_orders_push = models.BooleanField(default=True)
    restaurant_orders_email = models.BooleanField(default=True)
    restaurant_reviews_push = models.BooleanField(default=True)
    restaurant_reviews_email = models.BooleanField(default=True)
    
    # Driver notifications (for drivers)
    driver_assignments_push = models.BooleanField(default=True)
    driver_assignments_sms = models.BooleanField(default=True)
    
    # General settings
    do_not_disturb_start = models.TimeField(null=True, blank=True)
    do_not_disturb_end = models.TimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.full_name} - Notification Preferences"


class PushToken(models.Model):
    """
    Store push notification tokens for mobile devices
    """
    DEVICE_TYPES = (
        ('ios', 'iOS'),
        ('android', 'Android'),
        ('web', 'Web'),
    )
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='push_tokens')
    token = models.TextField()
    device_type = models.CharField(max_length=10, choices=DEVICE_TYPES)
    device_id = models.CharField(max_length=100, null=True, blank=True)
    
    is_active = models.BooleanField(default=True)
    last_used = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'token')
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['token']),
        ]
    
    def __str__(self):
        return f"{self.user.full_name} - {self.device_type} token"


class NotificationLog(models.Model):
    """
    Log of notification delivery attempts
    """
    notification = models.ForeignKey(Notification, on_delete=models.CASCADE, related_name='delivery_logs')
    delivery_method = models.CharField(max_length=10, choices=[
        ('push', 'Push Notification'),
        ('email', 'Email'),
        ('sms', 'SMS'),
    ])
    
    # Delivery status
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('failed', 'Failed'),
        ('bounced', 'Bounced'),
    ], default='pending')
    
    # Details
    provider = models.CharField(max_length=50, null=True, blank=True)  # e.g., 'firebase', 'twilio', 'sendgrid'
    provider_message_id = models.CharField(max_length=200, null=True, blank=True)
    error_message = models.TextField(null=True, blank=True)
    
    # Timestamps
    sent_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['notification', 'delivery_method']),
            models.Index(fields=['status', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.notification.title} - {self.delivery_method} - {self.status}"
