from rest_framework import serializers
from .models import Restaurant, Menu, MenuCategory, MenuItem, RestaurantReview

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
        fields = ['id', 'name', 'description', 'order', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

class MenuItemSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    restaurant_name = serializers.CharField(source='restaurant.name', read_only=True)
    menu_name = serializers.CharField(source='menu.name', read_only=True)
    
    class Meta:
        model = MenuItem
        fields = [
            'id', 'restaurant', 'restaurant_name', 'menu', 'menu_name', 'category', 'category_name',
            'name', 'description', 'price', 'currency', 'image', 'is_available', 'is_featured',
            'preparation_time', 'ingredients', 'allergens', 'calories', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

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
    class Meta:
        model = Restaurant
        fields = ['id', 'name', 'location_lat', 'location_lng', 'is_active', 'created_at']
        read_only_fields = ['id', 'created_at']

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