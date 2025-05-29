from datetime import datetime
from django.db import models
from django.conf import settings
from core.models import TimeStampedModel


class NotificationTemplate(TimeStampedModel):
    NOTIFICATION_TYPE_CHOICES = (
        ('ORDER_PLACED', 'Order Placed'),
        ('ORDER_CONFIRMED', 'Order Confirmed'),
        ('ORDER_PREPARING', 'Order Preparing'),
        ('ORDER_READY', 'Order Ready for Pickup'),
        ('ORDER_PICKED_UP', 'Order Picked Up'),
        ('ORDER_ON_THE_WAY', 'Order On the Way'),
        ('ORDER_DELIVERED', 'Order Delivered'),
        ('ORDER_CANCELLED', 'Order Cancelled'),
        ('PAYMENT_SUCCESS', 'Payment Successful'),
        ('PAYMENT_FAILED', 'Payment Failed'),
        ('DRIVER_ASSIGNED', 'Driver Assigned'),
        ('PROMOTION_AVAILABLE', 'Promotion Available'),
        ('LOYALTY_POINTS_EARNED', 'Loyalty Points Earned'),
        ('REFERRAL_REWARD', 'Referral Reward'),
        ('RESTAURANT_APPROVED', 'Restaurant Approved'),
        ('RESTAURANT_REJECTED', 'Restaurant Rejected'),
        ('SYSTEM_MAINTENANCE', 'System Maintenance'),
        ('WELCOME', 'Welcome Message'),
    )
    
    CHANNEL_CHOICES = (
        ('IN_APP', 'In-App Notification'),
        ('EMAIL', 'Email'),
        ('SMS', 'SMS'),
        ('PUSH', 'Push Notification'),
    )
    
    type = models.CharField(max_length=30, choices=NOTIFICATION_TYPE_CHOICES, unique=True)
    name = models.CharField(max_length=100)
    
    # Template content for different channels
    in_app_title = models.CharField(max_length=200, blank=True)
    in_app_message = models.TextField(blank=True)
    
    email_subject = models.CharField(max_length=200, blank=True)
    email_template = models.TextField(blank=True)
    
    sms_message = models.CharField(max_length=160, blank=True)
    
    push_title = models.CharField(max_length=100, blank=True)
    push_message = models.CharField(max_length=200, blank=True)
    
    # Channels where this notification should be sent
    enabled_channels = models.JSONField(default=list)  # ['IN_APP', 'EMAIL', 'PUSH']
    
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.name} ({self.get_type_display()})"


class Notification(TimeStampedModel):
    PRIORITY_CHOICES = (
        ('LOW', 'Low'),
        ('NORMAL', 'Normal'),
        ('HIGH', 'High'),
        ('URGENT', 'Urgent'),
    )
    
    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('SENT', 'Sent'),
        ('DELIVERED', 'Delivered'),
        ('READ', 'Read'),
        ('FAILED', 'Failed'),
    )
    
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    template = models.ForeignKey(NotificationTemplate, on_delete=models.CASCADE, related_name='notifications')
    
    title = models.CharField(max_length=200)
    message = models.TextField()
    
    # Metadata
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='NORMAL')
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='PENDING')
    
    # Context data for template rendering
    context_data = models.JSONField(default=dict, blank=True)
    
    # Tracking
    sent_at = models.DateTimeField(null=True, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)
    
    # Related objects
    related_order = models.ForeignKey('orders.Order', on_delete=models.CASCADE, null=True, blank=True)
    related_restaurant = models.ForeignKey('restaurants.Restaurant', on_delete=models.CASCADE, null=True, blank=True)
    
    # Action button (optional)
    action_url = models.URLField(blank=True, null=True)
    action_text = models.CharField(max_length=50, blank=True, null=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} for {self.recipient.full_name}"
    
    def mark_as_read(self):
        if self.status != 'READ':
            self.status = 'READ'
            self.read_at = datetime.now()
            self.save()


class NotificationDelivery(TimeStampedModel):
    """Track delivery across different channels"""
    notification = models.ForeignKey(Notification, on_delete=models.CASCADE, related_name='deliveries')
    channel = models.CharField(max_length=10, choices=NotificationTemplate.CHANNEL_CHOICES)
    
    # Delivery details
    recipient_address = models.CharField(max_length=255)  # email, phone, device_token
    
    status = models.CharField(max_length=15, choices=Notification.STATUS_CHOICES, default='PENDING')
    
    # External service tracking
    external_id = models.CharField(max_length=100, blank=True, null=True)
    response_data = models.JSONField(default=dict, blank=True)
    
    sent_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    failed_at = models.DateTimeField(null=True, blank=True)
    failure_reason = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.notification.title} via {self.channel} to {self.recipient_address}"


class NotificationPreference(TimeStampedModel):
    """User preferences for different types of notifications"""
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notification_preferences')
    
    # Channel preferences
    enable_in_app = models.BooleanField(default=True)
    enable_email = models.BooleanField(default=True)
    enable_sms = models.BooleanField(default=False)
    enable_push = models.BooleanField(default=True)
    
    # Notification type preferences
    order_updates = models.BooleanField(default=True)
    payment_updates = models.BooleanField(default=True)
    promotional = models.BooleanField(default=True)
    driver_updates = models.BooleanField(default=True)
    restaurant_updates = models.BooleanField(default=True)
    system_updates = models.BooleanField(default=True)
    
    # Quiet hours
    quiet_hours_enabled = models.BooleanField(default=False)
    quiet_hours_start = models.TimeField(null=True, blank=True)
    quiet_hours_end = models.TimeField(null=True, blank=True)
    
    def __str__(self):
        return f"Notification preferences for {self.user.full_name}"


class DeviceToken(TimeStampedModel):
    """Store device tokens for push notifications"""
    DEVICE_TYPE_CHOICES = (
        ('IOS', 'iOS'),
        ('ANDROID', 'Android'),
        ('WEB', 'Web Browser'),
    )
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='device_tokens')
    token = models.TextField()
    device_type = models.CharField(max_length=10, choices=DEVICE_TYPE_CHOICES)
    device_name = models.CharField(max_length=100, blank=True)
    
    is_active = models.BooleanField(default=True)
    last_used = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('user', 'token')
    
    def __str__(self):
        return f"{self.device_type} token for {self.user.full_name}"


class NotificationBatch(TimeStampedModel):
    """For sending bulk notifications"""
    name = models.CharField(max_length=100)
    template = models.ForeignKey(NotificationTemplate, on_delete=models.CASCADE)
    
    # Targeting
    target_user_roles = models.JSONField(default=list)  # ['CUSTOMER', 'DRIVER']
    target_restaurants = models.ManyToManyField('restaurants.Restaurant', blank=True)
    target_cities = models.JSONField(default=list, blank=True)
    
    # Filters
    only_active_users = models.BooleanField(default=True)
    only_users_with_orders = models.BooleanField(default=False)
    min_orders_count = models.PositiveIntegerField(null=True, blank=True)
    
    # Scheduling
    scheduled_at = models.DateTimeField(null=True, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    
    # Stats
    total_recipients = models.PositiveIntegerField(default=0)
    successful_sends = models.PositiveIntegerField(default=0)
    failed_sends = models.PositiveIntegerField(default=0)
    
    status = models.CharField(max_length=15, default='DRAFT')  # DRAFT, SCHEDULED, SENDING, COMPLETED, FAILED
    
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    
    def __str__(self):
        return f"Batch: {self.name}"
