from rest_framework import serializers
from .models import Cart, CartItem, SavedCart, CartPromotion, CartAbandonment
from restaurants.serializers import MenuItemSerializer
from restaurants.models import MenuItem


class CartItemSerializer(serializers.ModelSerializer):
    menu_item_details = MenuItemSerializer(source='menu_item', read_only=True)
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    menu_item_name = serializers.CharField(source='menu_item.name', read_only=True)
    
    class Meta:
        model = CartItem
        fields = [
            'id', 'menu_item', 'menu_item_name', 'menu_item_details',
            'quantity', 'unit_price', 'special_instructions', 'subtotal',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'cart', 'unit_price', 'created_at', 'updated_at']


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    restaurant_name = serializers.CharField(source='restaurant.name', read_only=True)
    total_items = serializers.IntegerField(read_only=True)
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    estimated_delivery_fee = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    total = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    
    class Meta:
        model = Cart
        fields = [
            'id', 'user', 'restaurant', 'restaurant_name', 'items',
            'delivery_address', 'delivery_lat', 'delivery_lng', 'delivery_instructions',
            'requested_delivery_time', 'total_items', 'subtotal', 'estimated_delivery_fee',
            'total', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']


class AddToCartSerializer(serializers.Serializer):
    """
    Serializer for adding items to cart
    """
    menu_item_id = serializers.UUIDField()
    quantity = serializers.IntegerField(min_value=1, default=1)
    special_instructions = serializers.CharField(max_length=500, required=False, allow_blank=True)
    
    def validate_menu_item_id(self, value):
        """
        Validate that menu item exists and is available
        """
        try:
            menu_item = MenuItem.objects.get(id=value)
            if not menu_item.is_available:
                raise serializers.ValidationError("This menu item is currently unavailable.")
            return value
        except MenuItem.DoesNotExist:
            raise serializers.ValidationError("Menu item not found.")


class UpdateCartItemSerializer(serializers.Serializer):
    """
    Serializer for updating cart item quantity
    """
    quantity = serializers.IntegerField(min_value=0)
    special_instructions = serializers.CharField(max_length=500, required=False, allow_blank=True)


class SetDeliveryAddressSerializer(serializers.Serializer):
    """
    Serializer for setting delivery address
    """
    delivery_address = serializers.CharField(max_length=500)
    delivery_lat = serializers.DecimalField(max_digits=9, decimal_places=6, required=False)
    delivery_lng = serializers.DecimalField(max_digits=9, decimal_places=6, required=False)
    delivery_instructions = serializers.CharField(max_length=500, required=False, allow_blank=True)


class SavedCartSerializer(serializers.ModelSerializer):
    restaurant_name = serializers.CharField(source='restaurant.name', read_only=True)
    items_count = serializers.SerializerMethodField()
    estimated_total = serializers.SerializerMethodField()
    
    class Meta:
        model = SavedCart
        fields = [
            'id', 'name', 'restaurant', 'restaurant_name', 'cart_data',
            'is_favorite', 'times_reordered', 'last_ordered',
            'items_count', 'estimated_total', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'times_reordered', 'last_ordered', 'created_at', 'updated_at']
    
    def get_items_count(self, obj) -> int:
        """Get total number of items in saved cart"""
        return len(obj.cart_data.get('items', []))
    
    def get_estimated_total(self, obj) -> str:
        """Get estimated total from saved cart data"""
        return obj.cart_data.get('subtotal', '0.00')
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class SaveCartSerializer(serializers.Serializer):
    """
    Serializer for saving current cart
    """
    name = serializers.CharField(max_length=100)
    is_favorite = serializers.BooleanField(default=False)


class CartPromotionSerializer(serializers.ModelSerializer):
    promotion_name = serializers.CharField(source='promotion.name', read_only=True)
    promotion_code = serializers.CharField(source='promotion.code', read_only=True)
    
    class Meta:
        model = CartPromotion
        fields = [
            'id', 'promotion', 'promotion_name', 'promotion_code',
            'discount_amount', 'discount_percentage', 'applied_at'
        ]
        read_only_fields = ['id', 'cart', 'applied_at']


class ApplyPromotionSerializer(serializers.Serializer):
    """
    Serializer for applying promotion codes
    """
    promotion_code = serializers.CharField(max_length=50)


class CartAbandonmentSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.full_name', read_only=True)
    restaurant_name = serializers.CharField(source='restaurant.name', read_only=True)
    
    class Meta:
        model = CartAbandonment
        fields = [
            'id', 'user', 'user_name', 'session_key', 'restaurant', 'restaurant_name',
            'items_count', 'cart_value', 'cart_data', 'abandoned_at', 'abandonment_stage',
            'recovered', 'recovered_at', 'recovery_order', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class CartCheckoutSerializer(serializers.Serializer):
    """
    Serializer for cart checkout validation
    """
    delivery_address = serializers.CharField(max_length=500)
    delivery_lat = serializers.DecimalField(max_digits=9, decimal_places=6, required=False)
    delivery_lng = serializers.DecimalField(max_digits=9, decimal_places=6, required=False)
    delivery_instructions = serializers.CharField(max_length=500, required=False, allow_blank=True)
    payment_method = serializers.ChoiceField(choices=[
        ('card', 'Credit/Debit Card'),
        ('cash', 'Cash on Delivery'),
        ('wallet', 'Digital Wallet'),
    ])
    order_notes = serializers.CharField(max_length=500, required=False, allow_blank=True)
    
    def validate(self, data):
        """
        Validate checkout data
        """
        # Add any additional validation logic here
        return data


class CartSummarySerializer(serializers.Serializer):
    """
    Serializer for cart summary data
    """
    total_items = serializers.IntegerField()
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=2)
    delivery_fee = serializers.DecimalField(max_digits=10, decimal_places=2)
    tax_amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    discount_amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    total = serializers.DecimalField(max_digits=10, decimal_places=2)
    restaurant_name = serializers.CharField()
    estimated_delivery_time = serializers.IntegerField()  # in minutes
