from django.db import models
from django.conf import settings
from django.utils import timezone
import uuid


class Restaurant(models.Model):
    # Basic Restaurant Info
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='restaurants')  # Changed from OneToOne
    name = models.CharField(max_length=100)
    description = models.TextField()
    cuisine_type = models.CharField(max_length=50)
    price_range = models.CharField(max_length=10)  # $, $$, $$$, $$$$
    
    # Location & Address
    address = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    zip_code = models.CharField(max_length=20)
    country = models.CharField(max_length=100, default='United States')
    location_lat = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    location_lng = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    
    # Delivery Settings
    delivery_radius = models.FloatField(default=5.0)  # in miles
    delivery_fee = models.DecimalField(max_digits=10, decimal_places=2, default=2.99)
    minimum_order = models.DecimalField(max_digits=10, decimal_places=2, default=15.00)
    service_areas = models.JSONField(default=dict, blank=True)
    
    # Contact Information
    primary_phone = models.CharField(max_length=20)
    secondary_phone = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField()
    website = models.URLField(blank=True, null=True)
    
    # Social Media (JSON field)
    social_media = models.JSONField(default=dict, blank=True)  # {facebook, instagram, twitter, tiktok}
    
    # Contact Person
    contact_person = models.JSONField(default=dict, blank=True)  # {name, title, phone, email}
    
    # Emergency Contact
    emergency_contact = models.JSONField(default=dict, blank=True)  # {name, phone, relationship}
    
    # Branding
    logo = models.ImageField(upload_to='restaurant/logos/', null=True, blank=True)
    banner_image = models.ImageField(upload_to='restaurant/banners/', null=True, blank=True)
    brand_colors = models.JSONField(default=dict, blank=True)  # {primary, secondary, accent}
    tagline = models.CharField(max_length=200, blank=True, null=True)
    story = models.TextField(blank=True, null=True)
    specialties = models.JSONField(default=dict, blank=True)
    
    # Tags and Features
    tags = models.JSONField(default=dict, blank=True)
    special_diets = models.JSONField(default=dict, blank=True)
    accessibility_features = models.JSONField(default=dict, blank=True)
    
    # Facilities
    parking_available = models.BooleanField(default=False)
    
    # Status
    is_active = models.BooleanField(default=True)
    is_open = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name


class RestaurantOperatingHours(models.Model):
    """Operating hours for each day of the week"""
    DAYS_OF_WEEK = [
        ('monday', 'Monday'),
        ('tuesday', 'Tuesday'),
        ('wednesday', 'Wednesday'),
        ('thursday', 'Thursday'),
        ('friday', 'Friday'),
        ('saturday', 'Saturday'),
        ('sunday', 'Sunday'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='operating_hours')
    day_of_week = models.CharField(max_length=10, choices=DAYS_OF_WEEK)
    is_open = models.BooleanField(default=True)
    open_time = models.TimeField(null=True, blank=True)
    close_time = models.TimeField(null=True, blank=True)
    has_break = models.BooleanField(default=False)
    break_start = models.TimeField(null=True, blank=True)
    break_end = models.TimeField(null=True, blank=True)
    
    class Meta:
        unique_together = ('restaurant', 'day_of_week')
        ordering = ['day_of_week']
    
    def __str__(self):
        return f"{self.restaurant.name} - {self.get_day_of_week_display()}"


class RestaurantDeliveryHours(models.Model):
    """Delivery hours (can be different from operating hours)"""
    DAYS_OF_WEEK = [
        ('monday', 'Monday'),
        ('tuesday', 'Tuesday'),
        ('wednesday', 'Wednesday'),
        ('thursday', 'Thursday'),
        ('friday', 'Friday'),
        ('saturday', 'Saturday'),
        ('sunday', 'Sunday'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='delivery_hours')
    day_of_week = models.CharField(max_length=10, choices=DAYS_OF_WEEK)
    is_available = models.BooleanField(default=True)
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)
    
    class Meta:
        unique_together = ('restaurant', 'day_of_week')
        ordering = ['day_of_week']
    
    def __str__(self):
        return f"{self.restaurant.name} - Delivery {self.get_day_of_week_display()}"


class Menu(models.Model):
    """Menu model that can be associated with one or all restaurants of an owner"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='menus', null=True, blank=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='menus')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        if self.restaurant:
            return f"{self.name} - {self.restaurant.name}"
        return f"{self.name} - All Restaurants"


# Keep existing models for backwards compatibility
class MenuCategory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='menu/categories/', null=True, blank=True)
    order = models.PositiveIntegerField(default=0, help_text='Order of display')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        verbose_name_plural = 'Menu Categories'
        ordering = ['order', 'name']
    
    def __str__(self):
        return self.name


class MenuItem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='menu_items')
    menu = models.ForeignKey(Menu, on_delete=models.CASCADE, related_name='items', null=True, blank=True)
    category = models.ForeignKey(MenuCategory, on_delete=models.SET_NULL, related_name='items', null=True, blank=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to='restaurant/menu_items/', null=True, blank=True)
    is_available = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    preparation_time = models.PositiveIntegerField(help_text='Preparation time in minutes', null=True, blank=True)
    ingredients = models.TextField(blank=True, null=True, help_text='List of ingredients')
    allergens = models.TextField(blank=True, null=True, help_text='Allergen information')
    calories = models.PositiveIntegerField(null=True, blank=True, help_text='Calorie count')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['category__order', 'name']
    
    def __str__(self):
        return f"{self.restaurant.name} - {self.name}"


class RestaurantReview(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='restaurant_reviews')
    rating = models.PositiveSmallIntegerField(choices=[(i, i) for i in range(1, 6)])
    comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('restaurant', 'user')
    
    def __str__(self):
        return f"{self.restaurant.name} - {self.rating} stars by {self.user.email}"