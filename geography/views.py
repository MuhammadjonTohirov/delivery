from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend

from .models import Address, DeliveryZone, LocationHistory, DeliveryRoute, ServiceArea
from .serializers import (
    AddressSerializer, DeliveryZoneSerializer, LocationHistorySerializer,
    DeliveryRouteSerializer, ServiceAreaSerializer, DistanceCalculationSerializer,
    DeliveryFeeCalculationSerializer, GeocodeRequestSerializer, GeocodeResponseSerializer,
    RouteOptimizationSerializer, NearbyRestaurantsSerializer, DeliveryZoneCheckSerializer
)
from .utils import (
    calculate_distance, calculate_delivery_fee, estimate_delivery_time,
    find_optimal_route, is_point_in_radius, get_bounding_box
)
from users.permissions import IsOwnerOrAdmin, IsDriver
from restaurants.models import Restaurant
from drf_spectacular.utils import extend_schema, extend_schema_view


class AddressPermission(permissions.BasePermission):
    """
    Custom permission for addresses:
    - Users can only manage their own addresses
    - Admins can view all addresses
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        if request.user.is_staff:
            return True
        return obj.user == request.user


@extend_schema_view(
    list=extend_schema(summary="List user addresses", description="List user's saved addresses"),
    retrieve=extend_schema(summary="Get address", description="Get a specific address"),
    create=extend_schema(summary="Create address", description="Create a new address"),
    update=extend_schema(summary="Update address", description="Update an address"),
    partial_update=extend_schema(summary="Partial update address", description="Partially update an address"),
    destroy=extend_schema(summary="Delete address", description="Delete an address"),
)
class AddressViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing user addresses
    """
    serializer_class = AddressSerializer
    permission_classes = [AddressPermission]
    
    def get_queryset(self):
        user = self.request.user
        
        if user.is_staff:
            return Address.objects.all()
        
        return Address.objects.filter(user=user)
    
    @extend_schema(
        summary="Set default address",
        description="Set an address as the user's default address"
    )
    @action(detail=True, methods=['post'])
    def set_default(self, request, pk=None):
        """
        Set an address as the default address
        """
        address = self.get_object()
        
        # Remove default from other addresses
        Address.objects.filter(user=request.user, is_default=True).update(is_default=False)
        
        # Set this address as default
        address.is_default = True
        address.save()
        
        serializer = self.get_serializer(address)
        return Response(serializer.data)


@extend_schema_view(
    list=extend_schema(summary="List delivery zones", description="List delivery zones for restaurants"),
    retrieve=extend_schema(summary="Get delivery zone", description="Get a specific delivery zone"),
)
class DeliveryZoneViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing delivery zones
    """
    serializer_class = DeliveryZoneSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['restaurant', 'is_active']
    
    def get_queryset(self):
        return DeliveryZone.objects.filter(is_active=True)
    
    @extend_schema(
        summary="Check delivery availability",
        description="Check if delivery is available to a specific location"
    )
    @action(detail=False, methods=['post'])
    def check_delivery(self, request):
        """
        Check if delivery is available to a specific location
        """
        serializer = DeliveryZoneCheckSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        data = serializer.validated_data
        latitude = float(data['latitude'])
        longitude = float(data['longitude'])
        restaurant_id = data.get('restaurant_id')
        
        # Filter zones by restaurant if specified
        zones_qs = self.get_queryset()
        if restaurant_id:
            zones_qs = zones_qs.filter(restaurant_id=restaurant_id)
        
        # Check which zones contain the point
        available_zones = []
        for zone in zones_qs:
            if zone.contains_point(latitude, longitude):
                distance = calculate_distance(
                    float(zone.center_latitude), float(zone.center_longitude),
                    latitude, longitude
                )
                delivery_fee = calculate_delivery_fee(distance, zone.base_delivery_fee, zone.per_km_fee)
                estimated_time = estimate_delivery_time(distance, zone.estimated_delivery_time_minutes)
                
                available_zones.append({
                    'zone': DeliveryZoneSerializer(zone).data,
                    'distance_km': round(distance, 2),
                    'delivery_fee': delivery_fee,
                    'estimated_delivery_time': estimated_time
                })
        
        return Response({
            'delivery_available': len(available_zones) > 0,
            'available_zones': available_zones
        })


@extend_schema_view(
    list=extend_schema(summary="List location history", description="List location tracking history"),
    create=extend_schema(summary="Create location update", description="Create a new location update"),
)
class LocationHistoryViewSet(viewsets.ModelViewSet):
    """
    ViewSet for location tracking
    """
    serializer_class = LocationHistorySerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ['get', 'post', 'head', 'options']  # Only allow GET and POST
    
    def get_queryset(self):
        user = self.request.user
        
        if user.is_staff:
            return LocationHistory.objects.all()
        
        # Users can only see their own location history
        return LocationHistory.objects.filter(user=user)


@extend_schema_view(
    list=extend_schema(summary="List delivery routes", description="List delivery routes for drivers"),
    retrieve=extend_schema(summary="Get delivery route", description="Get a specific delivery route"),
)
class DeliveryRouteViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for delivery routes (read-only for now)
    """
    serializer_class = DeliveryRouteSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        
        if user.is_staff:
            return DeliveryRoute.objects.all()
        
        if user.is_driver() and hasattr(user, 'driver_profile'):
            return DeliveryRoute.objects.filter(driver=user.driver_profile)
        
        return DeliveryRoute.objects.none()


@extend_schema_view(
    list=extend_schema(summary="List service areas", description="List platform service areas"),
    retrieve=extend_schema(summary="Get service area", description="Get a specific service area"),
)
class ServiceAreaViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for service areas
    """
    serializer_class = ServiceAreaSerializer
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        return ServiceArea.objects.filter(is_active=True)


class GeographyUtilsViewSet(viewsets.ViewSet):
    """
    ViewSet for geography utility functions
    """
    permission_classes = [permissions.IsAuthenticated]
    
    @extend_schema(
        summary="Calculate distance",
        description="Calculate distance between two geographic points"
    )
    @action(detail=False, methods=['post'])
    def calculate_distance(self, request):
        """
        Calculate distance between two points
        """
        serializer = DistanceCalculationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        data = serializer.validated_data
        distance = calculate_distance(
            float(data['from_latitude']), float(data['from_longitude']),
            float(data['to_latitude']), float(data['to_longitude'])
        )
        
        return Response({
            'distance_km': round(distance, 3),
            'distance_miles': round(distance * 0.621371, 3)
        })
    
    @extend_schema(
        summary="Calculate delivery fee",
        description="Calculate delivery fee based on distance and restaurant settings"
    )
    @action(detail=False, methods=['post'])
    def calculate_delivery_fee(self, request):
        """
        Calculate delivery fee for a specific route
        """
        serializer = DeliveryFeeCalculationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        data = serializer.validated_data
        
        # Calculate distance
        distance = calculate_distance(
            float(data['restaurant_latitude']), float(data['restaurant_longitude']),
            float(data['delivery_latitude']), float(data['delivery_longitude'])
        )
        
        # Get restaurant-specific delivery zone settings if available
        restaurant_id = data.get('restaurant_id')
        base_fee = 2.50
        per_km_fee = 0.50
        
        if restaurant_id:
            try:
                restaurant = Restaurant.objects.get(id=restaurant_id)
                # Check if there are delivery zones for this restaurant
                zone = DeliveryZone.objects.filter(
                    restaurant=restaurant,
                    is_active=True
                ).first()
                
                if zone and zone.contains_point(
                    float(data['delivery_latitude']),
                    float(data['delivery_longitude'])
                ):
                    base_fee = float(zone.base_delivery_fee)
                    per_km_fee = float(zone.per_km_fee)
            except Restaurant.DoesNotExist:
                pass
        
        delivery_fee = calculate_delivery_fee(distance, base_fee, per_km_fee)
        estimated_time = estimate_delivery_time(distance)
        
        return Response({
            'distance_km': round(distance, 3),
            'delivery_fee': delivery_fee,
            'estimated_delivery_time_minutes': estimated_time,
            'base_fee': base_fee,
            'per_km_fee': per_km_fee
        })
    
    @extend_schema(
        summary="Optimize route",
        description="Optimize delivery route through multiple waypoints"
    )
    @action(detail=False, methods=['post'])
    def optimize_route(self, request):
        """
        Optimize route through multiple waypoints
        """
        serializer = RouteOptimizationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        data = serializer.validated_data
        pickup = data['pickup_location']
        deliveries = data['delivery_locations']
        
        # Optimize the route
        optimized_route = find_optimal_route([pickup] + deliveries)
        
        # Calculate total distance
        total_distance = 0
        for i in range(len(optimized_route) - 1):
            distance = calculate_distance(
                optimized_route[i]['lat'], optimized_route[i]['lng'],
                optimized_route[i + 1]['lat'], optimized_route[i + 1]['lng']
            )
            total_distance += distance
        
        return Response({
            'optimized_route': optimized_route,
            'total_distance_km': round(total_distance, 3),
            'estimated_duration_minutes': estimate_delivery_time(total_distance),
            'waypoint_count': len(optimized_route)
        })
    
    @extend_schema(
        summary="Find nearby restaurants",
        description="Find restaurants near a specific location"
    )
    @action(detail=False, methods=['post'])
    def nearby_restaurants(self, request):
        """
        Find restaurants near a specific location
        """
        serializer = NearbyRestaurantsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        data = serializer.validated_data
        latitude = float(data['latitude'])
        longitude = float(data['longitude'])
        radius_km = float(data['radius_km'])
        limit = data['limit']
        
        # Get bounding box for efficient database query
        bbox = get_bounding_box(latitude, longitude, radius_km)
        
        # Find restaurants within bounding box
        nearby_restaurants = Restaurant.objects.filter(
            location_lat__gte=bbox['min_lat'],
            location_lat__lte=bbox['max_lat'],
            location_lng__gte=bbox['min_lng'],
            location_lng__lte=bbox['max_lng'],
            location_lat__isnull=False,
            location_lng__isnull=False
        )
        
        # Calculate exact distances and filter by radius
        restaurant_distances = []
        for restaurant in nearby_restaurants:
            distance = calculate_distance(
                latitude, longitude,
                float(restaurant.location_lat), float(restaurant.location_lng)
            )
            
            if distance <= radius_km:
                restaurant_distances.append({
                    'restaurant': restaurant,
                    'distance_km': distance
                })
        
        # Sort by distance and limit results
        restaurant_distances.sort(key=lambda x: x['distance_km'])
        restaurant_distances = restaurant_distances[:limit]
        
        # Format response
        results = []
        for item in restaurant_distances:
            restaurant = item['restaurant']
            results.append({
                'id': restaurant.id,
                'name': restaurant.name,
                'address': restaurant.address,
                'distance_km': round(item['distance_km'], 2),
                'is_open': restaurant.is_open,
                'estimated_delivery_time': estimate_delivery_time(item['distance_km'])
            })
        
        return Response({
            'restaurants': results,
            'total_found': len(results),
            'search_radius_km': radius_km
        })
    
    @extend_schema(
        summary="Geocode address",
        description="Convert address to geographic coordinates (mock implementation)"
    )
    @action(detail=False, methods=['post'])
    def geocode(self, request):
        """
        Geocode an address to get coordinates
        Note: This is a mock implementation. In production, you'd integrate with a real geocoding service.
        """
        serializer = GeocodeRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        address = serializer.validated_data['address']
        use_cache = serializer.validated_data['use_cache']
        
        # Mock geocoding response
        # In production, this would call Google Maps API, Mapbox, or similar service
        mock_response = {
            'latitude': 40.7128,  # Example: NYC coordinates
            'longitude': -74.0060,
            'formatted_address': f"Formatted: {address}",
            'city': 'New York',
            'state': 'NY',
            'country': 'United States',
            'postal_code': '10001',
            'confidence_score': 0.95,
            'is_exact_match': True,
            'from_cache': False
        }
        
        response_serializer = GeocodeResponseSerializer(mock_response)
        return Response(response_serializer.data)
