from rest_framework import serializers
from django.db import transaction
from .models import Restaurant, MenuCategory, MenuItem, RestaurantReview
from users.models import CustomUser


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
        # This will be handled in the view to filter by restaurant
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
    menu_categories = serializers.SerializerMethodField()
    menu_items = MenuItemSerializer(many=True, read_only=True)
    average_rating = serializers.SerializerMethodField()
    owner_name = serializers.CharField(source='user.full_name', read_only=True)
    
    class Meta:
        model = Restaurant
        fields = [
            'id', 'user', 'name', 'address', 'location_lat', 'location_lng',
            'description', 'logo', 'is_open', 'opening_time', 'closing_time',
            'created_at', 'updated_at', 'menu_categories', 'menu_items',
            'average_rating', 'owner_name'
        ]
        read_only_fields = [
            'id', 'user', 'created_at', 'updated_at',
            'average_rating', 'owner_name'
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
        # The 'average_rating_annotated' field is added in RestaurantViewSet's get_queryset
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
            'is_open', 'average_rating', 'owner_name'
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
        # The restaurant context should be passed from the view
        restaurant = self.context.get('restaurant')
        if restaurant:
            items = obj.items.filter(restaurant=restaurant)
            return MenuItemSerializer(items, many=True).data
        return []