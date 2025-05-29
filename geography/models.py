from django.db import models
from django.conf import settings
from core.models import TimeStampedModel
from restaurants.models import Restaurant
from decimal import Decimal
import math


class City(TimeStampedModel):
    name = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    
    # Center coordinates
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    
    # Service availability
    is_service_available = models.BooleanField(default=False)
    timezone = models.CharField(max_length=50, default='UTC')
    
    # Operational details
    service_start_time = models.TimeField(null=True, blank=True)
    service_end_time = models.TimeField(null=True, blank=True)
    
    class Meta:
        verbose_name_plural = 'Cities'
        unique_together = ('name', 'state', 'country')
    
    def __str__(self):
        return f"{self.name}, {self.state}, {self.country}"


class DeliveryZone(TimeStampedModel):
    name = models.CharField(max_length=100)
    city = models.ForeignKey(City, on_delete=models.CASCADE, related_name='delivery_zones')
    
    # Zone definition (polygon coordinates)
    boundary_coordinates = models.JSONField(help_text="Array of lat/lng coordinates defining the zone boundary")
    
    # Pricing
    base_delivery_fee = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    per_km_rate = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    free_delivery_threshold = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Service parameters
    max_delivery_distance_km = models.DecimalField(max_digits=5, decimal_places=2, default=10)
    estimated_delivery_time_minutes = models.PositiveIntegerField(default=30)
    
    # Operational
    is_active = models.BooleanField(default=True)
    priority = models.PositiveIntegerField(default=1)  # Lower number = higher priority
    
    # Restrictions
    min_order_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    max_order_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    def __str__(self):
        return f"{self.name} - {self.city.name}"
    
    def calculate_delivery_fee(self, distance_km, order_amount):
        """Calculate delivery fee based on distance and order amount"""
        if self.free_delivery_threshold and order_amount >= self.free_delivery_threshold:
            return Decimal('0')
        
        fee = self.base_delivery_fee + (self.per_km_rate * Decimal(str(distance_km)))
        return fee
    
    def is_point_in_zone(self, latitude, longitude):
        """Check if a point is within the delivery zone boundary"""
        # Simple implementation - in production, use proper geospatial libraries
        # This is a placeholder for point-in-polygon calculation
        return True  # Simplified for now


class Address(TimeStampedModel):
    ADDRESS_TYPE_CHOICES = (
        ('HOME', 'Home'),
        ('WORK', 'Work'),
        ('OTHER', 'Other'),
    )
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='addresses')
    
    # Address details
    label = models.CharField(max_length=50, blank=True)  # "Home", "Office", etc.
    type = models.CharField(max_length=10, choices=ADDRESS_TYPE_CHOICES, default='HOME')
    
    street_address = models.TextField()
    apartment_unit = models.CharField(max_length=50, blank=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=100, default='United States')
    
    # Coordinates
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    
    # Delivery instructions
    delivery_instructions = models.TextField(blank=True)
    
    # Status
    is_default = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    
    # Zone association
    delivery_zone = models.ForeignKey(DeliveryZone, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        ordering = ['-is_default', '-created_at']
    
    def __str__(self):
        if self.label:
            return f"{self.label} - {self.street_address}"
        return self.street_address
    
    def get_full_address(self):
        """Return formatted full address"""
        parts = [self.street_address]
        if self.apartment_unit:
            parts.append(f"Apt {self.apartment_unit}")
        parts.extend([self.city, self.state, self.postal_code])
        return ", ".join(parts)


class RestaurantDeliveryZone(TimeStampedModel):
    """Many-to-many relationship between restaurants and delivery zones with custom parameters"""
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='delivery_zones')
    zone = models.ForeignKey(DeliveryZone, on_delete=models.CASCADE, related_name='restaurants')
    
    # Restaurant-specific overrides
    custom_delivery_fee = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    custom_min_order_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    custom_delivery_time = models.PositiveIntegerField(null=True, blank=True)
    
    is_active = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ('restaurant', 'zone')
    
    def __str__(self):
        return f"{self.restaurant.name} serves {self.zone.name}"
    
    def get_delivery_fee(self, distance_km, order_amount):
        """Get delivery fee with restaurant-specific overrides"""
        if self.custom_delivery_fee is not None:
            return self.custom_delivery_fee
        return self.zone.calculate_delivery_fee(distance_km, order_amount)


class DeliveryEstimate(TimeStampedModel):
    """Store delivery time estimates and pricing for address/restaurant combinations"""
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE)
    delivery_address = models.ForeignKey(Address, on_delete=models.CASCADE)
    
    # Distance and time
    distance_km = models.DecimalField(max_digits=6, decimal_places=2)
    estimated_time_minutes = models.PositiveIntegerField()
    
    # Pricing
    delivery_fee = models.DecimalField(max_digits=8, decimal_places=2)
    
    # Validity
    valid_until = models.DateTimeField()
    
    class Meta:
        unique_together = ('restaurant', 'delivery_address')
    
    def __str__(self):
        return f"Delivery from {self.restaurant.name} to {self.delivery_address}"


class ServiceArea(TimeStampedModel):
    """Overall service area definition"""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    
    # Geographic bounds
    north_bound = models.DecimalField(max_digits=9, decimal_places=6)
    south_bound = models.DecimalField(max_digits=9, decimal_places=6)
    east_bound = models.DecimalField(max_digits=9, decimal_places=6)
    west_bound = models.DecimalField(max_digits=9, decimal_places=6)
    
    # Service configuration
    is_active = models.BooleanField(default=True)
    launch_date = models.DateField(null=True, blank=True)
    
    # Contact info for the area
    support_phone = models.CharField(max_length=20, blank=True)
    support_email = models.EmailField(blank=True)
    
    def __str__(self):
        return self.name
    
    def contains_point(self, latitude, longitude):
        """Check if a point is within the service area bounds"""
        return (
            self.south_bound <= latitude <= self.north_bound and
            self.west_bound <= longitude <= self.east_bound
        )


class LocationSearchCache(TimeStampedModel):
    """Cache for location searches to improve performance"""
    search_query = models.CharField(max_length=255, unique=True)
    
    # Geocoding results
    formatted_address = models.TextField()
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    
    # Additional data
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    
    # Cache metadata
    hit_count = models.PositiveIntegerField(default=0)
    last_accessed = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Cache: {self.search_query} -> {self.formatted_address}"


def calculate_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two points using Haversine formula"""
    # Convert latitude and longitude from degrees to radians
    lat1, lon1, lat2, lon2 = map(math.radians, [float(lat1), float(lon1), float(lat2), float(lon2)])
    
    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    # Radius of earth in kilometers
    r = 6371
    
    return c * r
