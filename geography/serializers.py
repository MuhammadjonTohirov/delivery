from rest_framework import serializers
from .models import Address, DeliveryZone, LocationHistory, GeocodingCache, DeliveryRoute, ServiceArea
from .utils import validate_coordinates, calculate_distance


class AddressSerializer(serializers.ModelSerializer):
    full_address = serializers.CharField(read_only=True)
    
    class Meta:
        model = Address
        fields = [
            'id', 'user', 'label', 'street_address', 'apartment_unit', 'city',
            'state', 'postal_code', 'country', 'latitude', 'longitude',
            'delivery_instructions', 'is_default', 'is_verified', 'full_address',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']
    
    def validate(self, data):
        """
        Validate coordinates if provided
        """
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        
        if latitude is not None and longitude is not None:
            if not validate_coordinates(float(latitude), float(longitude)):
                raise serializers.ValidationError(
                    "Invalid coordinates. Latitude must be between -90 and 90, longitude between -180 and 180."
                )
        
        return data
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class DeliveryZoneSerializer(serializers.ModelSerializer):
    restaurant_name = serializers.CharField(source='restaurant.name', read_only=True)
    
    class Meta:
        model = DeliveryZone
        fields = [
            'id', 'name', 'restaurant', 'restaurant_name', 'center_latitude',
            'center_longitude', 'radius_km', 'base_delivery_fee', 'per_km_fee',
            'estimated_delivery_time_minutes', 'is_active', 'priority',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class LocationHistorySerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.full_name', read_only=True)
    order_id = serializers.UUIDField(source='order.id', read_only=True)
    
    class Meta:
        model = LocationHistory
        fields = [
            'id', 'user', 'user_name', 'order', 'order_id', 'latitude', 'longitude',
            'accuracy', 'altitude', 'speed', 'activity_type', 'device_info',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class GeocodingCacheSerializer(serializers.ModelSerializer):
    class Meta:
        model = GeocodingCache
        fields = '__all__'


class DeliveryRouteSerializer(serializers.ModelSerializer):
    driver_name = serializers.CharField(source='driver.user.full_name', read_only=True)
    order_count = serializers.SerializerMethodField()
    
    class Meta:
        model = DeliveryRoute
        fields = [
            'id', 'driver', 'driver_name', 'total_distance_km', 'estimated_duration_minutes',
            'actual_duration_minutes', 'route_waypoints', 'optimization_algorithm',
            'status', 'started_at', 'completed_at', 'order_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_order_count(self, obj):
        return obj.orders.count()


class ServiceAreaSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceArea
        fields = [
            'id', 'name', 'code', 'center_latitude', 'center_longitude', 'radius_km',
            'is_active', 'launch_date', 'timezone', 'min_order_value',
            'max_delivery_distance_km', 'average_delivery_time_minutes',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class DistanceCalculationSerializer(serializers.Serializer):
    """
    Serializer for distance calculation requests
    """
    from_latitude = serializers.DecimalField(max_digits=9, decimal_places=6)
    from_longitude = serializers.DecimalField(max_digits=9, decimal_places=6)
    to_latitude = serializers.DecimalField(max_digits=9, decimal_places=6)
    to_longitude = serializers.DecimalField(max_digits=9, decimal_places=6)
    
    def validate(self, data):
        # Validate all coordinates
        for field in ['from_latitude', 'from_longitude', 'to_latitude', 'to_longitude']:
            value = data[field]
            if field.endswith('latitude'):
                if not -90 <= value <= 90:
                    raise serializers.ValidationError(f"{field} must be between -90 and 90")
            else:  # longitude
                if not -180 <= value <= 180:
                    raise serializers.ValidationError(f"{field} must be between -180 and 180")
        
        return data


class DeliveryFeeCalculationSerializer(serializers.Serializer):
    """
    Serializer for delivery fee calculation
    """
    restaurant_latitude = serializers.DecimalField(max_digits=9, decimal_places=6)
    restaurant_longitude = serializers.DecimalField(max_digits=9, decimal_places=6)
    delivery_latitude = serializers.DecimalField(max_digits=9, decimal_places=6)
    delivery_longitude = serializers.DecimalField(max_digits=9, decimal_places=6)
    restaurant_id = serializers.UUIDField(required=False)


class GeocodeRequestSerializer(serializers.Serializer):
    """
    Serializer for geocoding requests
    """
    address = serializers.CharField(max_length=500)
    use_cache = serializers.BooleanField(default=True)


class GeocodeResponseSerializer(serializers.Serializer):
    """
    Serializer for geocoding responses
    """
    latitude = serializers.DecimalField(max_digits=9, decimal_places=6, allow_null=True)
    longitude = serializers.DecimalField(max_digits=9, decimal_places=6, allow_null=True)
    formatted_address = serializers.CharField(allow_null=True)
    city = serializers.CharField(allow_null=True)
    state = serializers.CharField(allow_null=True)
    country = serializers.CharField(allow_null=True)
    postal_code = serializers.CharField(allow_null=True)
    confidence_score = serializers.FloatField(allow_null=True)
    is_exact_match = serializers.BooleanField()
    from_cache = serializers.BooleanField()


class RouteOptimizationSerializer(serializers.Serializer):
    """
    Serializer for route optimization requests
    """
    pickup_location = serializers.DictField(
        child=serializers.DecimalField(max_digits=9, decimal_places=6)
    )
    delivery_locations = serializers.ListField(
        child=serializers.DictField(
            child=serializers.DecimalField(max_digits=9, decimal_places=6)
        )
    )
    
    def validate_pickup_location(self, value):
        if 'lat' not in value or 'lng' not in value:
            raise serializers.ValidationError("Pickup location must have 'lat' and 'lng' keys")
        return value
    
    def validate_delivery_locations(self, value):
        for i, location in enumerate(value):
            if 'lat' not in location or 'lng' not in location:
                raise serializers.ValidationError(
                    f"Delivery location {i} must have 'lat' and 'lng' keys"
                )
        return value


class NearbyRestaurantsSerializer(serializers.Serializer):
    """
    Serializer for finding nearby restaurants
    """
    latitude = serializers.DecimalField(max_digits=9, decimal_places=6)
    longitude = serializers.DecimalField(max_digits=9, decimal_places=6)
    radius_km = serializers.DecimalField(max_digits=5, decimal_places=2, default=10)
    limit = serializers.IntegerField(min_value=1, max_value=100, default=20)


class DeliveryZoneCheckSerializer(serializers.Serializer):
    """
    Serializer for checking if an address is in delivery zone
    """
    latitude = serializers.DecimalField(max_digits=9, decimal_places=6)
    longitude = serializers.DecimalField(max_digits=9, decimal_places=6)
    restaurant_id = serializers.UUIDField(required=False)
