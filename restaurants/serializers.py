from rest_framework import serializers
from django.db import transaction
from .models import Restaurant, MenuCategory, MenuItem, RestaurantReview, RestaurantOperatingHours, RestaurantDeliveryHours
from users.models import CustomUser


class RestaurantOperatingHoursSerializer(serializers.ModelSerializer):
    class Meta:
        model = RestaurantOperatingHours
        fields = [
            'id', 'day_of_week', 'is_open', 'open_time', 'close_time',
            'has_break', 'break_start', 'break_end'
        ]
        read_only_fields = ['id']


class RestaurantDeliveryHoursSerializer(serializers.ModelSerializer):
    class Meta:
        model = RestaurantDeliveryHours
        fields = [
            'id', 'day_of_week', 'is_available', 'start_time', 'end_time'
        ]
        read_only_fields = ['id']


class RestaurantWizardSerializer(serializers.ModelSerializer):
    """
    Comprehensive serializer for restaurant creation via wizard
    """
    operating_hours = RestaurantOperatingHoursSerializer(many=True, required=False)
    delivery_hours = RestaurantDeliveryHoursSerializer(many=True, required=False)
    
    class Meta:
        model = Restaurant
        fields = [
            # Basic Info
            'id', 'name', 'description', 'cuisine_type', 'price_range',
            'tags', 'special_diets',
            
            # Location
            'address', 'city', 'state', 'zip_code', 'country',
            'location_lat', 'location_lng',
            
            # Delivery Settings
            'delivery_radius', 'delivery_fee', 'minimum_order', 'service_areas',
            
            # Contact Information
            'primary_phone', 'secondary_phone', 'email', 'website',
            'social_media', 'contact_person', 'emergency_contact',
            
            # Branding
            'logo', 'banner_image', 'brand_colors', 'tagline', 'story', 'specialties',
            
            # Facilities
            'accessibility_features', 'parking_available',
            
            # Hours
            'operating_hours', 'delivery_hours',
            
            # Status
            'is_active', 'is_open',
            
            # Timestamps
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate_primary_phone(self, value):
        """Validate primary phone number"""
        if not value or len(value.strip()) < 10:
            raise serializers.ValidationError("Primary phone number is required and must be at least 10 characters.")
        return value
    
    def validate_email(self, value):
        """Validate email address"""
        if not value or '@' not in value:
            raise serializers.ValidationError("Valid email address is required.")
        return value
    
    def validate_name(self, value):
        """Validate restaurant name"""
        if not value or len(value.strip()) < 2:
            raise serializers.ValidationError("Restaurant name is required and must be at least 2 characters.")
        return value
    
    def validate_description(self, value):
        """Validate description"""
        if not value or len(value.strip()) < 20:
            raise serializers.ValidationError("Description is required and must be at least 20 characters.")
        return value
    
    def validate_tagline(self, value):
        """Validate tagline"""
        if value and len(value) > 200:
            raise serializers.ValidationError("Tagline must be less than 200 characters.")
        return value
    
    def validate_story(self, value):
        """Validate story"""
        if value and len(value.strip()) < 50:
            raise serializers.ValidationError("Story must be at least 50 characters if provided.")
        return value
    
    def validate_delivery_radius(self, value):
        """Validate delivery radius"""
        if value is not None and (value < 1 or value > 50):
            raise serializers.ValidationError("Delivery radius must be between 1 and 50 miles.")
        return value
    
    def validate_delivery_fee(self, value):
        """Validate delivery fee"""
        if value is not None and (value < 0 or value > 20):
            raise serializers.ValidationError("Delivery fee must be between $0 and $20.")
        return value
    
    def validate_minimum_order(self, value):
        """Validate minimum order"""
        if value is not None and (value < 0 or value > 100):
            raise serializers.ValidationError("Minimum order must be between $0 and $100.")
        return value
    
    @transaction.atomic
    def create(self, validated_data):
        """Create restaurant with all related data"""
        operating_hours_data = validated_data.pop('operating_hours', [])
        delivery_hours_data = validated_data.pop('delivery_hours', [])
        
        # Create the restaurant
        restaurant = Restaurant.objects.create(**validated_data)
        
        # Create operating hours
        for hours_data in operating_hours_data:
            RestaurantOperatingHours.objects.create(
                restaurant=restaurant,
                **hours_data
            )
        
        # Create delivery hours
        for hours_data in delivery_hours_data:
            RestaurantDeliveryHours.objects.create(
                restaurant=restaurant,
                **hours_data
            )
        
        return restaurant
    
    @transaction.atomic
    def update(self, instance, validated_data):
        """Update restaurant with all related data"""
        operating_hours_data = validated_data.pop('operating_hours', [])
        delivery_hours_data = validated_data.pop('delivery_hours', [])
        
        # Update restaurant fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Update operating hours
        if operating_hours_data:
            # Clear existing hours and create new ones
            instance.operating_hours.all().delete()
            for hours_data in operating_hours_data:
                RestaurantOperatingHours.objects.create(
                    restaurant=instance,
                    **hours_data
                )
        
        # Update delivery hours
        if delivery_hours_data:
            # Clear existing hours and create new ones
            instance.delivery_hours.all().delete()
            for hours_data in delivery_hours_data:
                RestaurantDeliveryHours.objects.create(
                    restaurant=instance,
                    **hours_data
                )
        
        return instance


class MenuItemSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    restaurant_name = serializers.CharField(source='restaurant.name', read_only=True)
    
    class Meta:
        model = MenuItem
        fields = [
            'id', 'restaurant', 'restaurant_name', 'category', 'category_name', 
            'name', 'description', 'price', 'image', 'is_available', 'is_featured', 
            'preparation_time', 'ingredients', 'allergens', 'calories',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'restaurant_name', 'category_name', 
            'created_at', 'updated_at'
        ]
    
    def validate_price(self, value):
        """Ensure price is positive"""
        if value <= 0:
            raise serializers.ValidationError("Price must be greater than zero.")
        return value


class MenuCategorySerializer(serializers.ModelSerializer):
    items_count = serializers.SerializerMethodField()
    
    class Meta:
        model = MenuCategory
        fields = [
            'id', 'name', 'description', 'order', 'is_active',
            'items_count', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'items_count', 'created_at', 'updated_at'
        ]
    
    def get_items_count(self, obj):
        """Get count of items in this category for the current restaurant context"""
        return getattr(obj, 'items_count', 0)


class RestaurantReviewSerializer(serializers.ModelSerializer):
    user_full_name = serializers.CharField(source='user.full_name', read_only=True)
    
    class Meta:
        model = RestaurantReview
        fields = [
            'id', 'restaurant', 'user', 'user_full_name', 'rating', 
            'comment', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'user', 'user_full_name', 'created_at', 'updated_at'
        ]


class RestaurantSerializer(serializers.ModelSerializer):
    """Enhanced restaurant serializer with all wizard data"""
    menu_categories = serializers.SerializerMethodField()
    menu_items = MenuItemSerializer(many=True, read_only=True)
    average_rating = serializers.SerializerMethodField()
    owner_name = serializers.CharField(source='user.full_name', read_only=True)
    operating_hours = RestaurantOperatingHoursSerializer(many=True, read_only=True)
    delivery_hours = RestaurantDeliveryHoursSerializer(many=True, read_only=True)
    
    class Meta:
        model = Restaurant
        fields = [
            # Basic Info
            'id', 'name', 'description', 'cuisine_type', 'price_range',
            'tags', 'special_diets',
            
            # Location
            'address', 'city', 'state', 'zip_code', 'country',
            'location_lat', 'location_lng',
            
            # Delivery Settings
            'delivery_radius', 'delivery_fee', 'minimum_order', 'service_areas',
            
            # Contact Information
            'primary_phone', 'secondary_phone', 'email', 'website',
            'social_media', 'contact_person', 'emergency_contact',
            
            # Branding
            'logo', 'banner_image', 'brand_colors', 'tagline', 'story', 'specialties',
            
            # Facilities
            'accessibility_features', 'parking_available',
            
            # Hours
            'operating_hours', 'delivery_hours',
            
            # Status
            'is_active', 'is_open',
            
            # Related Data
            'menu_categories', 'menu_items', 'average_rating', 'owner_name',
            
            # Timestamps
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at',
            'average_rating', 'owner_name', 'menu_categories', 'menu_items'
        ]
    
    def get_menu_categories(self, obj):
        """Get categories that have items in this restaurant"""
        from django.db.models import Count
        categories = MenuCategory.objects.filter(
            items__restaurant=obj
        ).annotate(
            items_count=Count('items')
        ).distinct().order_by('order', 'name')
        
        return MenuCategorySerializer(categories, many=True).data
    
    def get_average_rating(self, obj) -> float | None:
        """
        Retrieve the pre-calculated average rating from the annotated field.
        """
        if hasattr(obj, 'average_rating_annotated') and obj.average_rating_annotated is not None:
            return round(obj.average_rating_annotated, 1)
        return None


class RestaurantListSerializer(serializers.ModelSerializer):
    """
    Simplified serializer for listing restaurants.
    """
    average_rating = serializers.SerializerMethodField()
    owner_name = serializers.CharField(source='user.full_name', read_only=True)
    
    class Meta:
        model = Restaurant
        fields = [
            'id', 'name', 'address', 'description', 'logo', 
            'is_open', 'average_rating', 'owner_name', 'cuisine_type', 'price_range'
        ]
    
    def get_average_rating(self, obj) -> float | None:
        """
        Calculate the average rating for the restaurant.
        """
        if hasattr(obj, 'average_rating_annotated') and obj.average_rating_annotated is not None:
            return round(obj.average_rating_annotated, 1)
            
        reviews = obj.reviews.all()
        if reviews.exists():
            total = sum(review.rating for review in reviews)
            return round(total / reviews.count(), 1)
        return None


class MenuCategoryWithItemsSerializer(MenuCategorySerializer):
    """
    Extended serializer for menu categories that includes items for a specific restaurant.
    """
    items = serializers.SerializerMethodField()
    
    class Meta(MenuCategorySerializer.Meta):
        pass
    
    def get_items(self, obj):
        """Get items in this category for the current restaurant context"""
        restaurant = self.context.get('restaurant')
        if restaurant:
            items = obj.items.filter(restaurant=restaurant)
            return MenuItemSerializer(items, many=True).data
        return []