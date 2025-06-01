from django.db import models
from django.conf import settings
from core.models import TimeStampedModel
import uuid


class Address(TimeStampedModel):
    """
    Standardized address model for deliveries
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='addresses')
    
    # Address details
    label = models.CharField(max_length=50, null=True, blank=True)  # e.g., "Home", "Work", "Office"
    street_address = models.CharField(max_length=200)
    apartment_unit = models.CharField(max_length=50, null=True, blank=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=100, default='United States')
    
    # Geographic coordinates
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    
    # Additional details
    delivery_instructions = models.TextField(null=True, blank=True)
    is_default = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-is_default', '-created_at']
        indexes = [
            models.Index(fields=['user', 'is_default']),
            models.Index(fields=['latitude', 'longitude']),
            models.Index(fields=['city', 'state']),
        ]
    
    def __str__(self):
        return f"{self.user.full_name} - {self.label or 'Address'}"
    
    def save(self, *args, **kwargs):
        # Ensure only one default address per user
        if self.is_default:
            Address.objects.filter(user=self.user, is_default=True).update(is_default=False)
        super().save(*args, **kwargs)
    
    @property
    def full_address(self):
        """
        Get formatted full address
        """
        parts = [self.street_address]
        if self.apartment_unit:
            parts.append(f"Apt {self.apartment_unit}")
        parts.extend([self.city, f"{self.state} {self.postal_code}", self.country])
        return ", ".join(parts)


class DeliveryZone(TimeStampedModel):
    """
    Delivery zones for restaurants and service areas
    """
    name = models.CharField(max_length=100)
    restaurant = models.ForeignKey('restaurants.Restaurant', on_delete=models.CASCADE, related_name='delivery_zones', null=True, blank=True)
    
    # Zone boundaries (simplified polygon using center + radius)
    center_latitude = models.DecimalField(max_digits=9, decimal_places=6)
    center_longitude = models.DecimalField(max_digits=9, decimal_places=6)
    radius_km = models.DecimalField(max_digits=5, decimal_places=2, default=5.0)  # Delivery radius in kilometers
    
    # Pricing and timing
    base_delivery_fee = models.DecimalField(max_digits=6, decimal_places=2, default=2.50)
    per_km_fee = models.DecimalField(max_digits=4, decimal_places=2, default=0.50)
    estimated_delivery_time_minutes = models.IntegerField(default=30)
    
    # Availability
    is_active = models.BooleanField(default=True)
    priority = models.IntegerField(default=1)  # Higher priority zones are checked first
    
    class Meta:
        ordering = ['-priority', 'name']
        indexes = [
            models.Index(fields=['restaurant', 'is_active']),
            models.Index(fields=['center_latitude', 'center_longitude']),
        ]
    
    def __str__(self):
        restaurant_name = self.restaurant.name if self.restaurant else "Platform"
        return f"{restaurant_name} - {self.name}"
    
    def contains_point(self, latitude, longitude):
        """
        Check if a point is within this delivery zone
        """
        from .utils import calculate_distance
        
        distance = calculate_distance(
            self.center_latitude, self.center_longitude,
            latitude, longitude
        )
        return distance <= float(self.radius_km)


class LocationHistory(TimeStampedModel):
    """
    Track location history for drivers and delivery tracking
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='location_history')
    order = models.ForeignKey('orders.Order', on_delete=models.CASCADE, null=True, blank=True, related_name='location_updates')
    
    # Location data
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    accuracy = models.FloatField(null=True, blank=True)  # GPS accuracy in meters
    altitude = models.FloatField(null=True, blank=True)
    speed = models.FloatField(null=True, blank=True)  # Speed in km/h
    
    # Context
    activity_type = models.CharField(max_length=20, choices=[
        ('IDLE', 'Idle'),
        ('DRIVING', 'Driving'),
        ('WALKING', 'Walking'),
        ('PICKUP', 'At Pickup Location'),
        ('DELIVERY', 'At Delivery Location'),
    ], default='IDLE')
    
    # Metadata
    device_info = models.JSONField(default=dict, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['order', 'created_at']),
            models.Index(fields=['latitude', 'longitude']),
        ]
    
    def __str__(self):
        return f"{self.user.full_name} location at {self.created_at}"


class GeocodingCache(models.Model):
    """
    Cache geocoding results to avoid repeated API calls
    """
    address_hash = models.CharField(max_length=64, unique=True)  # Hash of normalized address
    original_address = models.TextField()
    
    # Geocoded results
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    formatted_address = models.TextField(null=True, blank=True)
    
    # Administrative details
    city = models.CharField(max_length=100, null=True, blank=True)
    state = models.CharField(max_length=100, null=True, blank=True)
    country = models.CharField(max_length=100, null=True, blank=True)
    postal_code = models.CharField(max_length=20, null=True, blank=True)
    
    # Geocoding metadata
    provider = models.CharField(max_length=50, null=True, blank=True)  # e.g., 'google', 'mapbox'
    confidence_score = models.FloatField(null=True, blank=True)
    is_exact_match = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    last_used = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['address_hash']),
            models.Index(fields=['latitude', 'longitude']),
        ]
    
    def __str__(self):
        return f"Geocoding: {self.original_address[:50]}"


class DeliveryRoute(TimeStampedModel):
    """
    Optimized delivery routes for drivers
    """
    driver = models.ForeignKey('users.DriverProfile', on_delete=models.CASCADE, related_name='delivery_routes')
    orders = models.ManyToManyField('orders.Order', related_name='delivery_routes')
    
    # Route details
    total_distance_km = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    estimated_duration_minutes = models.IntegerField(null=True, blank=True)
    actual_duration_minutes = models.IntegerField(null=True, blank=True)
    
    # Route optimization data
    route_waypoints = models.JSONField(default=list, blank=True)  # List of lat/lng coordinates
    optimization_algorithm = models.CharField(max_length=50, default='nearest_neighbor')
    
    # Status
    status = models.CharField(max_length=20, choices=[
        ('PLANNED', 'Planned'),
        ('ACTIVE', 'Active'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    ], default='PLANNED')
    
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['driver', 'status']),
            models.Index(fields=['status', 'created_at']),
        ]
    
    def __str__(self):
        return f"Route for {self.driver.user.full_name} - {self.orders.count()} orders"


class ServiceArea(models.Model):
    """
    Platform service areas and coverage zones
    """
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True)  # e.g., 'NYC_MANHATTAN', 'LA_DOWNTOWN'
    
    # Geographic boundaries
    center_latitude = models.DecimalField(max_digits=9, decimal_places=6)
    center_longitude = models.DecimalField(max_digits=9, decimal_places=6)
    radius_km = models.DecimalField(max_digits=6, decimal_places=2)
    
    # Service details
    is_active = models.BooleanField(default=True)
    launch_date = models.DateField(null=True, blank=True)
    timezone = models.CharField(max_length=50, default='UTC')
    
    # Operational settings
    min_order_value = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    max_delivery_distance_km = models.DecimalField(max_digits=5, decimal_places=2, default=10)
    average_delivery_time_minutes = models.IntegerField(default=35)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['is_active']),
            models.Index(fields=['center_latitude', 'center_longitude']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.code})"
