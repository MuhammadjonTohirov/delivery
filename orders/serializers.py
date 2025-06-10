from django.db.models import Avg
from rest_framework import serializers
from .models import Order, OrderItem, OrderStatusUpdate
from users.models import CustomUser # Added
from restaurants.models import MenuItem, Restaurant, RestaurantReview # Added RestaurantReview
from django.db import transaction
from django.utils import timezone

# --- Detail Serializers ---

class CustomerDetailSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='full_name')

    class Meta:
        model = CustomUser
        fields = ['id', 'name', 'phone']
        read_only_fields = ['id', 'name', 'phone']


class RestaurantDetailSerializer(serializers.ModelSerializer):
    cuisine = serializers.SerializerMethodField()
    rating = serializers.SerializerMethodField()
    deliveryTime = serializers.SerializerMethodField()

    class Meta:
        model = Restaurant
        fields = ['id', 'name', 'cuisine', 'rating', 'deliveryTime']
        read_only_fields = ['id', 'name', 'cuisine', 'rating', 'deliveryTime']

    def get_cuisine(self, obj):
        # Placeholder: Restaurant model does not have a cuisine field
        return "To be implemented" # Or None

    def get_rating(self, obj):
        # Calculate average rating from RestaurantReview
        average_rating = RestaurantReview.objects.filter(restaurant=obj).aggregate(Avg('rating'))['rating__avg']
        return round(average_rating, 1) if average_rating else None

    def get_deliveryTime(self, obj):
        # Placeholder: Restaurant model does not have a deliveryTime field
        return "To be implemented" # Or None


class CoordinatesSerializer(serializers.Serializer): # Must be defined before DeliveryAddressSerializer
    latitude = serializers.DecimalField(max_digits=9, decimal_places=6, source='delivery_lat', required=False, allow_null=True)
    longitude = serializers.DecimalField(max_digits=9, decimal_places=6, source='delivery_lng', required=False, allow_null=True)


class DeliveryAddressSerializer(serializers.ModelSerializer):
    street = serializers.SerializerMethodField()
    city = serializers.SerializerMethodField()
    state = serializers.SerializerMethodField()
    zipCode = serializers.SerializerMethodField()
    country = serializers.SerializerMethodField()
    fullAddress = serializers.CharField(source='delivery_address', read_only=True)
    coordinates = CoordinatesSerializer(source='*', read_only=True)
    mapImageUrl = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = ['street', 'city', 'state', 'zipCode', 'country', 'fullAddress', 'coordinates', 'mapImageUrl']
        read_only_fields = fields

    def get_street(self, obj):
        # Placeholder: Order.delivery_address is a single TextField. Parsing logic would go here.
        return None

    def get_city(self, obj):
        # Placeholder
        return None

    def get_state(self, obj):
        # Placeholder
        return None

    def get_zipCode(self, obj):
        # Placeholder
        return None

    def get_country(self, obj):
        # Placeholder
        return None

    def get_mapImageUrl(self, obj):
        # Placeholder: No map image URL in the model
        return "https://maps.example.com/staticmap?center=..." # Or None


# --- Existing Serializers ---

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
    items = OrderItemSerializer(many=True, read_only=True) # Added for order items
    status_display = serializers.CharField(source='get_status_display', read_only=True) # Added for display status

    class Meta:
        model = Order
        fields = ['id', 'customer_name', 'restaurant_name', 'status', 'status_display',
                  'delivery_address', 'delivery_fee', 'notes', # Added fields
                  'total_price', 'created_at', 'item_count', 'items'] # Added items

    def get_item_count(self, obj) -> int:
        return obj.items.count()


# --- Additional Detail Serializers ---

class OrderItemDetailSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='menu_item.name', read_only=True)
    description = serializers.CharField(source='menu_item.description', read_only=True)
    totalPrice = serializers.SerializerMethodField(read_only=True)
    imageUrl = serializers.ImageField(source='menu_item.image', read_only=True, allow_null=True)
    category = serializers.CharField(source='menu_item.category.name', read_only=True, allow_null=True)
    customizations = serializers.SerializerMethodField(read_only=True) # Placeholder
    specialInstructions = serializers.CharField(source='notes', read_only=True, allow_null=True)
    unitPrice = serializers.DecimalField(source='unit_price', max_digits=10, decimal_places=2, read_only=True)


    class Meta:
        model = OrderItem
        fields = ['id', 'name', 'description', 'quantity', 'unitPrice', 'totalPrice',
                  'imageUrl', 'category', 'customizations', 'specialInstructions']
        read_only_fields = ['id', 'name', 'description', 'quantity', 'unitPrice', 'totalPrice',
                            'imageUrl', 'category', 'customizations', 'specialInstructions']

    def get_totalPrice(self, obj):
        return obj.quantity * obj.unit_price

    def get_customizations(self, obj):
        # Placeholder for customizations
        return []


class PricingDetailSerializer(serializers.ModelSerializer):
    subtotal = serializers.SerializerMethodField()
    serviceFee = serializers.SerializerMethodField() # Placeholder
    tax = serializers.SerializerMethodField() # Placeholder
    tip = serializers.SerializerMethodField() # Placeholder
    total = serializers.DecimalField(source='total_price', max_digits=10, decimal_places=2, read_only=True)
    deliveryFee = serializers.DecimalField(source='delivery_fee', max_digits=10, decimal_places=2, read_only=True)
    # discount is already on Order model

    class Meta:
        model = Order
        fields = ['subtotal', 'deliveryFee', 'serviceFee', 'tax', 'tip', 'discount', 'total']
        read_only_fields = fields

    def get_subtotal(self, obj):
        # Sum of all order item subtotals
        return sum(item.subtotal for item in obj.items.all())

    def get_serviceFee(self, obj):
        # Placeholder
        return None

    def get_tax(self, obj):
        # Placeholder
        return None

    def get_tip(self, obj):
        # Placeholder
        return None


class PaymentDetailSerializer(serializers.Serializer): # No model backing this directly for now
    method = serializers.SerializerMethodField()
    cardLast4 = serializers.SerializerMethodField()
    cardType = serializers.SerializerMethodField()
    transactionId = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()

    class Meta:
        fields = ['method', 'cardLast4', 'cardType', 'transactionId', 'status']
        read_only_fields = fields

    def get_method(self, obj):
        return "Placeholder Payment Method" # e.g., "Credit Card"

    def get_cardLast4(self, obj):
        return "0000" # Placeholder

    def get_cardType(self, obj):
        return "Visa" # Placeholder

    def get_transactionId(self, obj):
        return "placeholder_transaction_id" # Placeholder

    def get_status(self, obj):
        return "Completed" # Placeholder, assumes payment was successful for a retrieved order


class DriverDetailSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='full_name', read_only=True)
    rating = serializers.SerializerMethodField() # Placeholder

    class Meta:
        model = CustomUser # Assuming driver is a CustomUser
        fields = ['id', 'name', 'phone', 'rating']
        read_only_fields = ['id', 'name', 'phone', 'rating']

    def get_rating(self, obj):
        # Placeholder: Driver rating not on CustomUser model
        return None # Or a default like 5.0


class DeliveryDetailSerializer(serializers.ModelSerializer):
    type = serializers.SerializerMethodField() # Placeholder
    estimatedTime = serializers.DateTimeField(source='estimated_delivery_time', read_only=True)
    actualDeliveryTime = serializers.SerializerMethodField() # Placeholder
    # Assuming 'driver' might be a ForeignKey on Order or accessed via a related model like DriverTask
    # For now, this will be None if not directly on Order.
    driver = DriverDetailSerializer(read_only=True, allow_null=True, required=False)
    instructions = serializers.CharField(source='notes', read_only=True, allow_null=True) # Using order notes as delivery instructions

    class Meta:
        model = Order
        fields = ['type', 'estimatedTime', 'actualDeliveryTime', 'driver', 'instructions']
        read_only_fields = fields

    def get_type(self, obj):
        # Placeholder
        return "Standard Delivery"

    def get_actualDeliveryTime(self, obj):
        # Placeholder: This would be set when the order is actually delivered
        return None


class OrderStatusEventSerializer(serializers.ModelSerializer):
    timestamp = serializers.DateTimeField(source='created_at', read_only=True)
    completed = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = OrderStatusUpdate
        fields = ['status', 'timestamp', 'completed']
        read_only_fields = fields

    def get_completed(self, obj):
        # 'obj' is an OrderStatusUpdate instance.
        order_current_status = self.context.get('order_current_status')
        # An event is "completed" if its status is different from the order's current overall status.
        # This is a simplification; a more complex system might have a defined flow.
        if order_current_status:
            return obj.status != order_current_status
        # Fallback if context isn't provided, though it always should be by OrderStatusDetailSerializer.
        # Consider if this event is the *absolute latest* update for the order. If not, it's 'completed'.
        # However, this requires comparing its timestamp to the latest overall, which is tricky here.
        # The current logic relies on `order_current_status` being correctly passed.
        return False


class OrderStatusDetailSerializer(serializers.ModelSerializer):
    current = serializers.CharField(source='status', read_only=True) # Current status of the Order
    timeline = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Order # Source is the Order model
        fields = ['current', 'timeline']
        read_only_fields = fields

    def get_timeline(self, obj):
        # 'obj' is an Order instance.
        # status_updates are ordered by '-created_at' by default in OrderStatusUpdate.Meta
        status_updates = obj.status_updates.all()
        # Provide the order's current status to the event serializer's context
        context = {**self.context, 'order_current_status': obj.status}
        return OrderStatusEventSerializer(status_updates, many=True, context=context, read_only=True).data


class OrderTimestampDetailSerializer(serializers.ModelSerializer):
    ordered = serializers.SerializerMethodField()
    confirmed = serializers.SerializerMethodField()
    delivered = serializers.SerializerMethodField()

    class Meta:
        model = Order # Source is the Order model
        fields = ['ordered', 'confirmed', 'delivered']
        read_only_fields = fields

    def get_timestamp_for_status(self, obj, status_value):
        # Helper to get the creation timestamp of the first status update matching status_value
        status_update = obj.status_updates.filter(status=status_value).order_by('created_at').first()
        return status_update.created_at if status_update else None

    def get_ordered(self, obj):
        # Timestamp of the 'PLACED' status
        return self.get_timestamp_for_status(obj, 'PLACED')

    def get_confirmed(self, obj):
        # Timestamp of the 'CONFIRMED' status
        return self.get_timestamp_for_status(obj, 'CONFIRMED')

    def get_delivered(self, obj):
        # Timestamp of the 'DELIVERED' status
        return self.get_timestamp_for_status(obj, 'DELIVERED')


class OrderDetailSerializer(serializers.ModelSerializer):
    orderNumber = serializers.CharField(source='id', read_only=True) # Using UUID as orderNumber for simplicity
    status = OrderStatusDetailSerializer(source='*', read_only=True) # Pass the whole Order instance
    restaurant = RestaurantDetailSerializer(read_only=True)
    customer = CustomerDetailSerializer(read_only=True)
    deliveryAddress = DeliveryAddressSerializer(source='*', read_only=True) # Pass the whole Order instance
    pricing = PricingDetailSerializer(source='*', read_only=True) # Pass the whole Order instance
    payment = PaymentDetailSerializer(source='*', read_only=True) # Pass the whole Order instance (all placeholders)
    delivery = DeliveryDetailSerializer(source='*', read_only=True) # Pass the whole Order instance
    timestamps = OrderTimestampDetailSerializer(source='*', read_only=True) # Pass the whole Order instance

    class Meta:
        model = Order
        fields = [
            'id', 'orderNumber', 'status', 'restaurant', 'customer',
            'deliveryAddress', 'items', 'pricing', 'payment', 'delivery', 'timestamps'
        ]
        # All fields are read-only as this is a "Detail" serializer for retrieve actions
        read_only_fields = fields