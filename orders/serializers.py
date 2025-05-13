from rest_framework import serializers
from .models import Order, OrderItem, OrderStatusUpdate
from restaurants.models import MenuItem, Restaurant
from django.db import transaction
from django.utils import timezone


class OrderItemSerializer(serializers.ModelSerializer):
    menu_item_name = serializers.CharField(source='menu_item.name', read_only=True)
    
    class Meta:
        model = OrderItem
        fields = ['id', 'menu_item', 'menu_item_name', 'quantity', 'unit_price', 'subtotal', 'notes']
        read_only_fields = ['id', 'unit_price', 'subtotal', 'menu_item_name']
    
    def validate_menu_item(self, value):
        if not value.is_available:
            raise serializers.ValidationError(f"The menu item '{value.name}' is currently unavailable.")
        return value


class OrderStatusUpdateSerializer(serializers.ModelSerializer):
    updated_by_name = serializers.CharField(source='updated_by.full_name', read_only=True)
    
    class Meta:
        model = OrderStatusUpdate
        fields = ['id', 'status', 'updated_by', 'updated_by_name', 'notes', 'created_at']
        read_only_fields = ['id', 'updated_by', 'updated_by_name', 'created_at']
    
    def create(self, validated_data):
        validated_data['updated_by'] = self.context['request'].user
        return super().create(validated_data)


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True)
    customer_name = serializers.CharField(source='customer.full_name', read_only=True)
    restaurant_name = serializers.CharField(source='restaurant.name', read_only=True)
    status_updates = OrderStatusUpdateSerializer(many=True, read_only=True)
    
    class Meta:
        model = Order
        fields = ['id', 'customer', 'customer_name', 'restaurant', 'restaurant_name', 
                  'status', 'delivery_address', 'delivery_lat', 'delivery_lng', 
                  'total_price', 'delivery_fee', 'estimated_delivery_time', 
                  'notes', 'created_at', 'updated_at', 'items', 'status_updates']
        read_only_fields = ['id', 'customer', 'customer_name', 'restaurant_name', 
                           'total_price', 'created_at', 'updated_at', 'status_updates']
    
    def validate(self, data):
        # Check if items exist and restaurant matches
        items_data = data.get('items', [])
        if not items_data:
            raise serializers.ValidationError({"items": "Order must contain at least one item."})
        
        restaurant = data.get('restaurant')
        for item_data in items_data:
            menu_item = item_data.get('menu_item')
            if menu_item.restaurant != restaurant:
                raise serializers.ValidationError(
                    {"items": f"Menu item '{menu_item.name}' does not belong to the selected restaurant."}
                )
        
        return data
    
    @transaction.atomic
    def create(self, validated_data):
        # Extract and remove nested items data
        items_data = validated_data.pop('items')
        
        # Set customer to the current user
        validated_data['customer'] = self.context['request'].user
        
        # Calculate total price
        total_price = 0
        for item_data in items_data:
            menu_item = item_data['menu_item']
            quantity = item_data['quantity']
            total_price += menu_item.price * quantity
        
        # Add delivery fee to total price
        delivery_fee = validated_data.get('delivery_fee', 0)
        validated_data['total_price'] = total_price + delivery_fee
        
        # Create the order
        order = Order.objects.create(**validated_data)
        
        # Create order items
        for item_data in items_data:
            menu_item = item_data['menu_item']
            quantity = item_data['quantity']
            notes = item_data.get('notes', '')
            
            OrderItem.objects.create(
                order=order,
                menu_item=menu_item,
                quantity=quantity,
                unit_price=menu_item.price,
                subtotal=menu_item.price * quantity,
                notes=notes
            )
        
        # Create the initial status update
        OrderStatusUpdate.objects.create(
            order=order,
            status='PLACED',
            updated_by=self.context['request'].user,
            notes="Order placed by customer."
        )
        
        return order


class OrderUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating order status.
    """
    status_note = serializers.CharField(write_only=True, required=False, allow_blank=True)
    
    class Meta:
        model = Order
        fields = ['status', 'status_note']
    
    def update(self, instance, validated_data):
        status = validated_data.get('status', instance.status)
        status_note = validated_data.pop('status_note', '')
        
        # Update the order status
        instance.status = status
        instance.save()
        
        # Create a status update record
        OrderStatusUpdate.objects.create(
            order=instance,
            status=status,
            updated_by=self.context['request'].user,
            notes=status_note
        )
        
        return instance


class OrderListSerializer(serializers.ModelSerializer):
    """
    Simplified serializer for listing orders.
    """
    customer_name = serializers.CharField(source='customer.full_name', read_only=True)
    restaurant_name = serializers.CharField(source='restaurant.name', read_only=True)
    item_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Order
        fields = ['id', 'customer_name', 'restaurant_name', 'status', 
                  'total_price', 'created_at', 'item_count']
    
    def get_item_count(self, obj):
        return obj.items.count()