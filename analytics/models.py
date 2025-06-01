from django.db import models
from django.conf import settings
from core.models import TimeStampedModel
import uuid


class AnalyticsEvent(TimeStampedModel):
    """
    Model to track various analytics events in the platform
    """
    EVENT_TYPES = (
        ('ORDER_PLACED', 'Order Placed'),
        ('ORDER_DELIVERED', 'Order Delivered'),
        ('ORDER_CANCELLED', 'Order Cancelled'),
        ('USER_REGISTERED', 'User Registered'),
        ('RESTAURANT_VIEWED', 'Restaurant Viewed'),
        ('MENU_ITEM_VIEWED', 'Menu Item Viewed'),
        ('SEARCH_PERFORMED', 'Search Performed'),
        ('DRIVER_ASSIGNED', 'Driver Assigned'),
        ('REVIEW_SUBMITTED', 'Review Submitted'),
    )
    
    event_type = models.CharField(max_length=50, choices=EVENT_TYPES)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    restaurant = models.ForeignKey('restaurants.Restaurant', on_delete=models.SET_NULL, null=True, blank=True)
    order = models.ForeignKey('orders.Order', on_delete=models.SET_NULL, null=True, blank=True)
    menu_item = models.ForeignKey('restaurants.MenuItem', on_delete=models.SET_NULL, null=True, blank=True)
    
    # Additional data stored as JSON
    metadata = models.JSONField(default=dict, blank=True)
    
    # Location data
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    
    # Session and device info
    session_id = models.CharField(max_length=100, null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['event_type', 'created_at']),
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['restaurant', 'created_at']),
            models.Index(fields=['order', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.event_type} - {self.created_at}"


class DashboardStats(models.Model):
    """
    Pre-calculated dashboard statistics for performance
    """
    restaurant = models.ForeignKey('restaurants.Restaurant', on_delete=models.CASCADE, null=True, blank=True)
    date = models.DateField()
    
    # Order statistics
    total_orders = models.IntegerField(default=0)
    completed_orders = models.IntegerField(default=0)
    cancelled_orders = models.IntegerField(default=0)
    pending_orders = models.IntegerField(default=0)
    
    # Revenue statistics
    total_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    average_order_value = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Customer statistics
    new_customers = models.IntegerField(default=0)
    returning_customers = models.IntegerField(default=0)
    
    # Performance metrics
    average_preparation_time = models.IntegerField(default=0)  # in minutes
    average_delivery_time = models.IntegerField(default=0)   # in minutes
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('restaurant', 'date')
        ordering = ['-date']
        indexes = [
            models.Index(fields=['restaurant', 'date']),
            models.Index(fields=['date']),
        ]
    
    def __str__(self):
        restaurant_name = self.restaurant.name if self.restaurant else "Platform"
        return f"{restaurant_name} stats for {self.date}"


class RevenueMetrics(TimeStampedModel):
    """
    Detailed revenue tracking and metrics
    """
    restaurant = models.ForeignKey('restaurants.Restaurant', on_delete=models.CASCADE, null=True, blank=True)
    date = models.DateField()
    hour = models.IntegerField(null=True, blank=True)  # For hourly tracking
    
    # Revenue breakdown
    gross_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    net_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    delivery_fees = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    taxes = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    commission = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Order counts by type
    dine_in_orders = models.IntegerField(default=0)
    takeout_orders = models.IntegerField(default=0)
    delivery_orders = models.IntegerField(default=0)
    
    class Meta:
        unique_together = ('restaurant', 'date', 'hour')
        ordering = ['-date', '-hour']
        indexes = [
            models.Index(fields=['restaurant', 'date']),
            models.Index(fields=['date', 'hour']),
        ]
    
    def __str__(self):
        restaurant_name = self.restaurant.name if self.restaurant else "Platform"
        time_str = f"{self.date} {self.hour}:00" if self.hour is not None else str(self.date)
        return f"{restaurant_name} revenue for {time_str}"


class CustomerInsights(TimeStampedModel):
    """
    Customer behavior analytics
    """
    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    restaurant = models.ForeignKey('restaurants.Restaurant', on_delete=models.CASCADE, null=True, blank=True)
    
    # Customer metrics
    total_orders = models.IntegerField(default=0)
    total_spent = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    average_order_value = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Behavioral data
    favorite_cuisine = models.CharField(max_length=100, null=True, blank=True)
    preferred_order_time = models.CharField(max_length=20, null=True, blank=True)  # e.g., "evening", "lunch"
    last_order_date = models.DateTimeField(null=True, blank=True)
    
    # Engagement metrics
    app_opens = models.IntegerField(default=0)
    menu_views = models.IntegerField(default=0)
    search_count = models.IntegerField(default=0)
    
    class Meta:
        unique_together = ('customer', 'restaurant')
        indexes = [
            models.Index(fields=['customer']),
            models.Index(fields=['restaurant']),
            models.Index(fields=['total_spent']),
        ]
    
    def __str__(self):
        restaurant_name = self.restaurant.name if self.restaurant else "Platform"
        return f"{self.customer.full_name} insights for {restaurant_name}"


class PopularMenuItems(models.Model):
    """
    Track popular menu items for recommendations
    """
    menu_item = models.ForeignKey('restaurants.MenuItem', on_delete=models.CASCADE)
    restaurant = models.ForeignKey('restaurants.Restaurant', on_delete=models.CASCADE)
    date = models.DateField()
    
    # Metrics
    order_count = models.IntegerField(default=0)
    view_count = models.IntegerField(default=0)
    total_revenue = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Rankings
    popularity_rank = models.IntegerField(null=True, blank=True)
    revenue_rank = models.IntegerField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('menu_item', 'date')
        ordering = ['-order_count']
        indexes = [
            models.Index(fields=['restaurant', 'date']),
            models.Index(fields=['date', 'order_count']),
        ]
    
    def __str__(self):
        return f"{self.menu_item.name} on {self.date} - {self.order_count} orders"
