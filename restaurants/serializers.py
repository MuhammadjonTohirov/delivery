from rest_framework import serializers
from .models import Restaurant, MenuCategory, MenuItem, RestaurantReview
from users.models import CustomUser


class MenuItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = MenuItem
        fields = ['id', 'restaurant', 'category', 'name', 'description', 'price', 
                  'image', 'is_available', 'is_featured', 'preparation_time', 
                  'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate_restaurant(self, value):
        """
        Check that the restaurant belongs to the current user.
        """
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            if request.user.role == 'RESTAURANT' and hasattr(request.user, 'restaurant'):
                if request.user.restaurant != value:
                    raise serializers.ValidationError("You can only modify menu items for your own restaurant.")
            elif request.user.role != 'ADMIN':
                raise serializers.ValidationError("Only restaurant owners or admins can modify menu items.")
        return value


class MenuCategorySerializer(serializers.ModelSerializer):
    items = MenuItemSerializer(many=True, read_only=True)
    
    class Meta:
        model = MenuCategory
        fields = ['id', 'restaurant', 'name', 'description', 'order', 'items']
        read_only_fields = ['id']
    
    def validate_restaurant(self, value):
        """
        Check that the restaurant belongs to the current user.
        """
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            if request.user.role == 'RESTAURANT' and hasattr(request.user, 'restaurant'):
                if request.user.restaurant != value:
                    raise serializers.ValidationError("You can only modify categories for your own restaurant.")
            elif request.user.role != 'ADMIN':
                raise serializers.ValidationError("Only restaurant owners or admins can modify menu categories.")
        return value


class RestaurantReviewSerializer(serializers.ModelSerializer):
    user_full_name = serializers.CharField(source='user.full_name', read_only=True)
    
    class Meta:
        model = RestaurantReview
        fields = ['id', 'restaurant', 'user', 'user_full_name', 'rating', 'comment', 'created_at', 'updated_at']
        read_only_fields = ['id', 'user', 'created_at', 'updated_at', 'user_full_name']
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class RestaurantSerializer(serializers.ModelSerializer):
    menu_categories = MenuCategorySerializer(many=True, read_only=True)
    menu_items = MenuItemSerializer(many=True, read_only=True)
    average_rating = serializers.SerializerMethodField()
    owner_name = serializers.CharField(source='user.full_name', read_only=True)
    
    class Meta:
        model = Restaurant
        fields = ['id', 'user', 'name', 'address', 'location_lat', 'location_lng', 'description', 
                  'logo', 'is_open', 'opening_time', 'closing_time', 'created_at', 'updated_at',
                  'menu_categories', 'menu_items', 'average_rating', 'owner_name']
        read_only_fields = ['id', 'user', 'created_at', 'updated_at', 'average_rating', 'owner_name']
    
    def get_average_rating(self, obj):
        """
        Calculate the average rating for the restaurant.
        """
        reviews = obj.reviews.all()
        if reviews.exists():
            total = sum(review.rating for review in reviews)
            return round(total / reviews.count(), 1)
        return None
    
    def create(self, validated_data):
        """
        Create a restaurant and associate it with the current user.
        """
        user = self.context['request'].user
        
        # Check if user already has a restaurant
        if hasattr(user, 'restaurant'):
            raise serializers.ValidationError("User already has a restaurant.")
        
        validated_data['user'] = user
        return super().create(validated_data)


class RestaurantListSerializer(serializers.ModelSerializer):
    """
    Simplified serializer for listing restaurants.
    """
    average_rating = serializers.SerializerMethodField()
    owner_name = serializers.CharField(source='user.full_name', read_only=True)
    
    class Meta:
        model = Restaurant
        fields = ['id', 'name', 'address', 'description', 'logo', 'is_open', 
                  'average_rating', 'owner_name']
    
    def get_average_rating(self, obj):
        """
        Calculate the average rating for the restaurant.
        """
        reviews = obj.reviews.all()
        if reviews.exists():
            total = sum(review.rating for review in reviews)
            return round(total / reviews.count(), 1)
        return None