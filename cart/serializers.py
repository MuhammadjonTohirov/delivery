from rest_framework import serializers
from django.db import transaction
from .models import (
    Cart, CartItem, CartItemCustomization, MenuItemCustomization, 
    CustomizationOption, SavedCart, CustomerFavorite, RecentOrder, QuickReorder
)
from restaurants.models import MenuItem, Restaurant


class CustomizationOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomizationOption
        fields = ['id', 'name', 'description', 'additional_price', 'is_available', 'is_default', 'order']


class MenuItemCustomizationSerializer(serializers.ModelSerializer):
    options = CustomizationOptionSerializer(many=True, read_only=True)
    
    class Meta:
        model = MenuItemCustomization
        fields = ['id', 'name', 'description', 'type', 'is_required', 'min_selections', 
                  'max_selections', 'order', 'options']


class CartItemCustomizationSerializer(serializers.ModelSerializer):
    customization_name = serializers.CharField(source='customization.name', read_only=True)
    
    class Meta:
        model = CartItemCustomization
        fields = ['id', 'customization', 'customization_name', 'selected_options', 'additional_price']


class CartItemSerializer(serializers.ModelSerializer):
    menu_item_name = serializers.CharField(source='menu_item.name', read_only=True)
    menu_item_image = serializers.ImageField(source='menu_item.image', read_only=True)
    customizations = CartItemCustomizationSerializer(many=True, read_only=True)
    
    class Meta:
        model = CartItem
        fields = ['id', 'menu_item', 'menu_item_name', 'menu_item_image', 'quantity', 
                  'unit_price', 'total_price', 'special_instructions', 'customizations', 'created_at']
        read_only_fields = ['id', 'unit_price', 'total_price', 'created_at']


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    restaurant_name = serializers.CharField(source='restaurant.name', read_only=True)
    delivery_address_display = serializers.CharField(source='delivery_address.get_full_address', read_only=True)
    item_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Cart
        fields = ['id', 'restaurant', 'restaurant_name', 'subtotal', 'delivery_fee', 'tax_amount', 
                  'discount_amount', 'total', 'applied_coupon', 'loyalty_points_used', 
                  'delivery_address', 'delivery_address_display', 'delivery_instructions', 
                  'scheduled_for', 'items', 'item_count', 'last_modified']
        read_only_fields = ['id', 'subtotal', 'delivery_fee', 'tax_amount', 'discount_amount', 'total']
    
    def get_item_count(self, obj):
        return obj.item_count()


class AddToCartSerializer(serializers.Serializer):
    menu_item_id = serializers.UUIDField()
    quantity = serializers.IntegerField(min_value=1, default=1)
    special_instructions = serializers.CharField(required=False, allow_blank=True)
    customizations = serializers.ListField(
        child=serializers.DictField(), 
        required=False, 
        default=list
    )
    
    def validate_menu_item_id(self, value):
        try:
            menu_item = MenuItem.objects.get(id=value, is_available=True)
            return value
        except MenuItem.DoesNotExist:
            raise serializers.ValidationError("Menu item not found or unavailable.")
    
    def validate_customizations(self, value):
        # Validate customization data structure
        for customization in value:
            if 'customization_id' not in customization or 'selected_options' not in customization:
                raise serializers.ValidationError("Invalid customization format.")
        return value


class UpdateCartItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = CartItem
        fields = ['quantity', 'special_instructions']
    
    def validate_quantity(self, value):
        if value < 1:
            raise serializers.ValidationError("Quantity must be at least 1.")
        return value


class ApplyCouponSerializer(serializers.Serializer):
    coupon_code = serializers.CharField(max_length=20)
    
    def validate_coupon_code(self, value):
        from promotions.models import Coupon
        try:
            coupon = Coupon.objects.get(code=value.upper(), is_active=True)
            if not coupon.is_valid:
                raise serializers.ValidationError("This coupon is expired or no longer valid.")
            return value.upper()
        except Coupon.DoesNotExist:
            raise serializers.ValidationError("Invalid coupon code.")


class CustomerFavoriteSerializer(serializers.ModelSerializer):
    restaurant_name = serializers.CharField(source='restaurant.name', read_only=True)
    menu_item_name = serializers.CharField(source='menu_item.name', read_only=True)
    menu_item_image = serializers.ImageField(source='menu_item.image', read_only=True)
    
    class Meta:
        model = CustomerFavorite
        fields = ['id', 'type', 'restaurant', 'restaurant_name', 'menu_item', 
                  'menu_item_name', 'menu_item_image', 'notes', 'order_count', 'created_at']
        read_only_fields = ['id', 'order_count', 'created_at']
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class SavedCartSerializer(serializers.ModelSerializer):
    restaurant_name = serializers.CharField(source='restaurant.name', read_only=True)
    item_count = serializers.SerializerMethodField()
    
    class Meta:
        model = SavedCart
        fields = ['id', 'name', 'restaurant', 'restaurant_name', 'cart_data', 'item_count', 'created_at']
        read_only_fields = ['id', 'created_at']
    
    def get_item_count(self, obj):
        return len(obj.cart_data.get('items', []))
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class QuickReorderSerializer(serializers.ModelSerializer):
    restaurant_name = serializers.CharField(source='restaurant.name', read_only=True)
    item_count = serializers.SerializerMethodField()
    
    class Meta:
        model = QuickReorder
        fields = ['id', 'name', 'restaurant', 'restaurant_name', 'items_data', 
                  'item_count', 'last_used', 'use_count', 'created_at']
        read_only_fields = ['id', 'last_used', 'use_count', 'created_at']
    
    def get_item_count(self, obj):
        return len(obj.items_data.get('items', []))
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class RecentOrderSerializer(serializers.ModelSerializer):
    restaurant_name = serializers.CharField(source='restaurant.name', read_only=True)
    order_total = serializers.SerializerMethodField()
    
    class Meta:
        model = RecentOrder
        fields = ['id', 'restaurant', 'restaurant_name', 'order', 'order_summary', 
                  'order_total', 'created_at']
        read_only_fields = ['id', 'created_at']
    
    def get_order_total(self, obj):
        return obj.order_summary.get('total', 0)


class CheckoutSerializer(serializers.Serializer):
    """Serializer for cart checkout process"""
    delivery_address_id = serializers.UUIDField()
    payment_method_id = serializers.UUIDField()
    delivery_instructions = serializers.CharField(required=False, allow_blank=True)
    scheduled_for = serializers.DateTimeField(required=False)
    tip_amount = serializers.DecimalField(max_digits=8, decimal_places=2, required=False, default=0)
    
    def validate_delivery_address_id(self, value):
        from geography.models import Address
        try:
            address = Address.objects.get(id=value, user=self.context['request'].user)
            return value
        except Address.DoesNotExist:
            raise serializers.ValidationError("Invalid delivery address.")
    
    def validate_payment_method_id(self, value):
        from payments.models import PaymentMethod
        try:
            payment_method = PaymentMethod.objects.get(
                id=value, 
                user=self.context['request'].user, 
                is_active=True
            )
            return value
        except PaymentMethod.DoesNotExist:
            raise serializers.ValidationError("Invalid payment method.")


class CartRestaurantChangeSerializer(serializers.Serializer):
    """Serializer for changing restaurant (clears cart)"""
    restaurant_id = serializers.UUIDField()
    
    def validate_restaurant_id(self, value):
        try:
            restaurant = Restaurant.objects.get(id=value, is_open=True)
            return value
        except Restaurant.DoesNotExist:
            raise serializers.ValidationError("Restaurant not found or closed.")
