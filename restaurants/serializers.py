from rest_framework import serializers
from .models import Restaurant, Menu, MenuCategory, MenuItem, RestaurantReview
from utils.currency_helpers import format_price, get_currency_info

class MenuSerializer(serializers.ModelSerializer):
    restaurant_name = serializers.CharField(source='restaurant.name', read_only=True)
    
    class Meta:
        model = Menu
        fields = ['id', 'name', 'description', 'restaurant', 'restaurant_name', 'owner', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['id', 'owner', 'created_at', 'updated_at']
    
    def create(self, validated_data):
        validated_data['owner'] = self.context['request'].user
        return super().create(validated_data)

class MenuCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = MenuCategory
        fields = ['id', 'name', 'description', 'image', 'order', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

class MenuItemSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    restaurant_name = serializers.CharField(source='restaurant.name', read_only=True)
    menu_name = serializers.CharField(source='menu.name', read_only=True)
    formatted_price = serializers.SerializerMethodField()
    currency_info = serializers.SerializerMethodField()
    
    class Meta:
        model = MenuItem
        fields = [
            'id', 'restaurant', 'restaurant_name', 'menu', 'menu_name', 'category', 'category_name',
            'name', 'description', 'price', 'formatted_price', 'currency_info', 'image', 
            'is_available', 'is_featured', 'preparation_time', 'ingredients', 'allergens', 
            'calories', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'formatted_price', 'currency_info']
    
    def get_formatted_price(self, obj):
        """Return formatted price with currency symbol"""
        return format_price(obj.price)
    
    def get_currency_info(self, obj):
        """Return currency information"""
        return get_currency_info()

class RestaurantSerializer(serializers.ModelSerializer):
    menus = MenuSerializer(many=True, read_only=True)
    menu_items = MenuItemSerializer(many=True, read_only=True)
    
    class Meta:
        model = Restaurant
        fields = [
            'id', 'user', 'name', 'description', 'cuisine_type', 'price_range',
            'address', 'city', 'state', 'zip_code', 'country', 'location_lat', 'location_lng',
            'delivery_radius', 'delivery_fee', 'minimum_order', 'service_areas',
            'primary_phone', 'secondary_phone', 'email', 'website', 'social_media',
            'contact_person', 'emergency_contact', 'logo', 'banner_image', 'brand_colors',
            'tagline', 'story', 'specialties', 'tags', 'special_diets', 'accessibility_features',
            'parking_available', 'is_active', 'is_open', 'created_at', 'updated_at',
            'menus', 'menu_items'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

class RestaurantListSerializer(serializers.ModelSerializer):
    average_rating = serializers.SerializerMethodField()
    total_reviews = serializers.SerializerMethodField()
    estimated_delivery_time = serializers.SerializerMethodField()
    formatted_delivery_fee = serializers.SerializerMethodField()
    formatted_minimum_order = serializers.SerializerMethodField()
    
    class Meta:
        model = Restaurant
        fields = [
            'id', 'name', 'description', 'cuisine_type', 'price_range',
            'logo', 'banner_image', 'tagline', 'delivery_fee', 'minimum_order',
            'formatted_delivery_fee', 'formatted_minimum_order',
            'location_lat', 'location_lng', 'is_active', 'is_open',
            'average_rating', 'total_reviews', 'estimated_delivery_time',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_average_rating(self, obj):
        """Calculate average rating from reviews"""
        reviews = obj.reviews.all()
        if reviews.exists():
            return round(sum(review.rating for review in reviews) / len(reviews), 1)
        return 4.5  # Default rating if no reviews
    
    def get_total_reviews(self, obj):
        """Get total number of reviews"""
        return obj.reviews.count()
    
    def get_estimated_delivery_time(self, obj):
        """Calculate estimated delivery time in minutes"""
        # This could be more sophisticated based on distance, time of day, etc.
        # For now, return a base time (20-40 minutes) + some variation
        import random
        base_time = 25
        variation = random.randint(-5, 15)
        return max(15, base_time + variation)  # Minimum 15 minutes
    
    def get_formatted_delivery_fee(self, obj):
        """Return formatted delivery fee with currency symbol"""
        return format_price(obj.delivery_fee)
    
    def get_formatted_minimum_order(self, obj):
        """Return formatted minimum order with currency symbol"""
        return format_price(obj.minimum_order)

class RestaurantWizardSerializer(serializers.ModelSerializer):
    class Meta:
        model = Restaurant
        fields = [
            'id', 'user', 'name', 'description', 'cuisine_type', 'price_range',
            'address', 'city', 'state', 'zip_code', 'country', 'location_lat', 'location_lng',
            'delivery_radius', 'delivery_fee', 'minimum_order', 'service_areas',
            'primary_phone', 'secondary_phone', 'email', 'website', 'social_media',
            'contact_person', 'emergency_contact', 'logo', 'banner_image', 'brand_colors',
            'tagline', 'story', 'specialties', 'tags', 'special_diets', 'accessibility_features',
            'parking_available', 'is_active', 'is_open', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

class RestaurantReviewSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.full_name', read_only=True)
    restaurant_name = serializers.CharField(source='restaurant.name', read_only=True)
    
    class Meta:
        model = RestaurantReview
        fields = ['id', 'restaurant', 'restaurant_name', 'user', 'user_name', 'rating', 'comment', 'created_at', 'updated_at']
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)

class MenuCategoryWithItemsSerializer(serializers.ModelSerializer):
    items = serializers.SerializerMethodField()
    
    class Meta:
        model = MenuCategory
        fields = ['id', 'name', 'description', 'image', 'order', 'items']
    
    def get_items(self, obj):
        restaurant = self.context.get('restaurant')
        if restaurant:
            items = obj.items.filter(restaurant=restaurant, is_available=True)
            return MenuItemSerializer(items, many=True).data
        return []