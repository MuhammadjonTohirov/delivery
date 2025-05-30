from rest_framework import viewsets, permissions, status, filters, serializers
import uuid # Added for statistics pk conversion
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count, Avg, Q # Added Q for search queries
from .models import Restaurant, MenuCategory, MenuItem, RestaurantReview
from orders.models import Order # Added for statistics
from .serializers import (
    RestaurantSerializer, 
    RestaurantListSerializer,
    MenuCategorySerializer, 
    MenuItemSerializer, 
    RestaurantReviewSerializer
)
from users.permissions import IsRestaurantOwner, IsCustomer, IsOwnerOrAdmin
from drf_spectacular.utils import extend_schema, extend_schema_view


class RestaurantOwnerPermission(permissions.BasePermission):
    """
    Custom permission for restaurant owners.
    """
    def has_object_permission(self, request, view, obj):
        # Allow GET requests for all
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions only for restaurant owner or admin
        return obj.user == request.user or request.user.is_staff


@extend_schema_view(
    list=extend_schema(summary="List all restaurants", description="Get a list of all active restaurants"),
    retrieve=extend_schema(summary="Get restaurant details", description="Retrieve detailed information about a specific restaurant"),
    create=extend_schema(summary="Create restaurant", description="Create a new restaurant (Restaurant user only)"),
    update=extend_schema(summary="Update restaurant", description="Update restaurant details (Restaurant owner only)"),
    partial_update=extend_schema(summary="Partial update restaurant", description="Partially update restaurant details (Restaurant owner only)"),
)
class RestaurantViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Restaurant model.
    """
    queryset = Restaurant.objects.all() # Base queryset
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_open']
    search_fields = ['name', 'address']
    ordering_fields = ['name', 'created_at']

    def get_queryset(self):
        queryset = super().get_queryset() # Get the original queryset
        if self.action == 'list':
            queryset = queryset.annotate(average_rating_annotated=Avg('reviews__rating'))
        return queryset
    
    def get_serializer_class(self):
        if self.action == 'list':
            return RestaurantListSerializer
        return RestaurantSerializer
    
    def get_permissions(self):
        if self.action in ['update', 'partial_update', 'destroy']:
            permission_classes = [permissions.IsAuthenticated, RestaurantOwnerPermission]
        elif self.action == 'create':
            permission_classes = [permissions.IsAuthenticated, IsRestaurantOwner]
        else:
            permission_classes = [permissions.AllowAny]
        return [permission() for permission in permission_classes]

    @extend_schema(
        summary="Get restaurant menu",
        description="Get the full menu (categories and items) for a specific restaurant"
    )
    @action(detail=True, methods=['get'])
    def menu(self, request, pk=None):
        restaurant = self.get_object()
        categories = MenuCategory.objects.filter(restaurant=restaurant).prefetch_related('items')
        serializer = MenuCategorySerializer(categories, many=True)
        return Response(serializer.data)
    
    @extend_schema(
        summary="Get restaurant reviews",
        description="Get all reviews for a specific restaurant"
    )
    @action(detail=True, methods=['get'])
    def reviews(self, request, pk=None):
        restaurant = self.get_object()
        reviews = RestaurantReview.objects.filter(restaurant=restaurant)
        serializer = RestaurantReviewSerializer(reviews, many=True)
        return Response(serializer.data)

    @extend_schema(
        summary="Get my restaurant",
        description="Get the restaurant details for the currently authenticated restaurant owner."
    )
    @extend_schema(
        summary="Search restaurants and menu items",
        description="Advanced search across restaurants and menu items with filters"
    )
    @action(detail=False, methods=['get'])
    def search(self, request):
        query = request.query_params.get('q', '')
        cuisine = request.query_params.get('cuisine', '')
        min_rating = request.query_params.get('min_rating')
        delivery_fee_max = request.query_params.get('delivery_fee_max')
        is_open = request.query_params.get('is_open')
        
        restaurants = self.get_queryset()
        
        # Text search in name and description
        if query:
            restaurants = restaurants.filter(
                Q(name__icontains=query) | Q(description__icontains=query)
            )
        
        # Filter by cuisine (if you add cuisine field)
        # if cuisine:
        #     restaurants = restaurants.filter(cuisine__icontains=cuisine)
        
        # Filter by minimum rating
        if min_rating:
            restaurants = restaurants.filter(average_rating_annotated__gte=float(min_rating))
        
        # Filter by open status
        if is_open:
            restaurants = restaurants.filter(is_open=is_open.lower() == 'true')
        
        # Search in menu items as well
        menu_items = MenuItem.objects.filter(is_available=True)
        if query:
            menu_items = menu_items.filter(
                Q(name__icontains=query) | Q(description__icontains=query)
            )
            # Add restaurants that have matching menu items
            restaurant_ids_with_items = menu_items.values_list('restaurant_id', flat=True)
            restaurants = restaurants.filter(
                Q(id__in=restaurant_ids_with_items) | Q(id__in=restaurants.values_list('id', flat=True))
            ).distinct()
        
        serializer = self.get_serializer(restaurants, many=True)
        return Response({
            'restaurants': serializer.data,
            'total_count': restaurants.count()
        })
    
    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated, IsRestaurantOwner])
    def mine(self, request):
        try:
            restaurant = request.user.restaurant
            serializer = self.get_serializer(restaurant)
            return Response(serializer.data)
        except Restaurant.DoesNotExist:
            return Response(
                {"detail": "You do not have an associated restaurant."},
                status=status.HTTP_404_NOT_FOUND
            )
        except AttributeError: # If request.user doesn't have a 'restaurant' attribute
             return Response({"detail": "No restaurant associated with this user account."}, status=status.HTTP_404_NOT_FOUND)

@extend_schema_view(
    list=extend_schema(summary="List menu categories", description="List all menu categories for a restaurant"),
    retrieve=extend_schema(summary="Get menu category", description="Retrieve a specific menu category"),
    create=extend_schema(summary="Create menu category", description="Create a new menu category (Restaurant owner only)"),
    update=extend_schema(summary="Update menu category", description="Update a menu category (Restaurant owner only)"),
    partial_update=extend_schema(summary="Partial update menu category", description="Partially update a menu category (Restaurant owner only)"),
    destroy=extend_schema(summary="Delete menu category", description="Delete a menu category (Restaurant owner only)"),
)
class MenuCategoryViewSet(viewsets.ModelViewSet):
    """
    ViewSet for MenuCategory model.
    """
    serializer_class = MenuCategorySerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['restaurant']
    
    def get_queryset(self):
        # The filtering by restaurant_id from query_params will be handled by DjangoFilterBackend
        return MenuCategory.objects.all()
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [permissions.IsAuthenticated, IsRestaurantOwner]
        else:
            permission_classes = [permissions.AllowAny]
        return [permission() for permission in permission_classes]
    
    def perform_create(self, serializer):
        if self.request.user.is_staff:
            # Admin can create for any restaurant specified in payload
            # Ensure 'restaurant' is in validated_data or handle error
            if 'restaurant' not in serializer.validated_data:
                raise serializers.ValidationError({"restaurant": "Restaurant must be specified for admin creation."})
            serializer.save() # Restaurant is already in validated_data
        elif self.request.user.role == 'RESTAURANT' and hasattr(self.request.user, 'restaurant'):
            serializer.save(restaurant=self.request.user.restaurant)
        else:
            # This case should ideally be prevented by viewset permissions
            raise serializers.ValidationError("You do not have permission to create this resource here.")

@extend_schema_view(
    list=extend_schema(summary="List menu items", description="List all menu items, optionally filtered by restaurant"),
    retrieve=extend_schema(summary="Get menu item", description="Retrieve a specific menu item"),
    create=extend_schema(summary="Create menu item", description="Create a new menu item (Restaurant owner only)"),
    update=extend_schema(summary="Update menu item", description="Update a menu item (Restaurant owner only)"),
    partial_update=extend_schema(summary="Partial update menu item", description="Partially update a menu item (Restaurant owner only)"),
    destroy=extend_schema(summary="Delete menu item", description="Delete a menu item (Restaurant owner only)"),
)
class MenuItemViewSet(viewsets.ModelViewSet):
    """
    ViewSet for MenuItem model.
    """
    serializer_class = MenuItemSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['restaurant', 'category', 'is_available', 'is_featured']
    
    def get_queryset(self):
        return MenuItem.objects.all()
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [permissions.IsAuthenticated, IsRestaurantOwner]
        else:
            permission_classes = [permissions.AllowAny]
        return [permission() for permission in permission_classes]
    
    def perform_create(self, serializer):
        if self.request.user.is_staff:
            # Admin can create for any restaurant specified in payload
            # Ensure 'restaurant' is in validated_data or handle error
            if 'restaurant' not in serializer.validated_data:
                raise serializers.ValidationError({"restaurant": "Restaurant must be specified for admin creation."})
            serializer.save() # Restaurant is already in validated_data
        elif self.request.user.role == 'RESTAURANT' and hasattr(self.request.user, 'restaurant'):
            serializer.save(restaurant=self.request.user.restaurant)
        else:
            # This case should ideally be prevented by viewset permissions
            raise serializers.ValidationError("You do not have permission to create this resource here.")


@extend_schema_view(
    list=extend_schema(summary="List reviews", description="List all reviews for restaurants"),
    retrieve=extend_schema(summary="Get review", description="Retrieve a specific review"),
    create=extend_schema(summary="Create review", description="Create a new review (Customer only)"),
    update=extend_schema(summary="Update review", description="Update your own review (Customer only)"),
    partial_update=extend_schema(summary="Partial update review", description="Partially update your own review (Customer only)"),
    destroy=extend_schema(summary="Delete review", description="Delete your own review (Customer only)"),
)
class RestaurantReviewViewSet(viewsets.ModelViewSet):
    """
    ViewSet for RestaurantReview model.
    """
    serializer_class = RestaurantReviewSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['restaurant', 'user', 'rating']
    
    def get_queryset(self):
        return RestaurantReview.objects.all()
    
    def get_permissions(self):
        if self.action == 'create':
            permission_classes = [permissions.IsAuthenticated, IsCustomer]
        elif self.action in ['update', 'partial_update', 'destroy']:
            permission_classes = [permissions.IsAuthenticated, IsOwnerOrAdmin]
        else:
            permission_classes = [permissions.AllowAny]
        return [permission() for permission in permission_classes]
    

class RestaurantStatisticsView(viewsets.ViewSet):

    @extend_schema(
        summary="Get restaurant statistics",
        description="Get basic statistics for the currently authenticated restaurant owner's restaurant."
    )
    @action(detail=True, methods=['get'], permission_classes=[permissions.IsAuthenticated, IsRestaurantOwner])
    def get(self, request, pk=None):
        try:
            restaurant_obj = request.user.restaurant
            if pk and restaurant_obj.id != uuid.UUID(pk):
                 return Response({"detail": "Access to this restaurant's statistics is forbidden."}, status=status.HTTP_403_FORBIDDEN)
        except AttributeError:
            return Response({"detail": "No restaurant associated with this user account."}, status=status.HTTP_404_NOT_FOUND)

        total_orders = Order.objects.filter(restaurant=restaurant_obj).count()
        total_menu_items = MenuItem.objects.filter(restaurant=restaurant_obj).count()
        
        orders_by_status = Order.objects.filter(restaurant=restaurant_obj)\
            .values('status')\
            .annotate(count=Count('status'))\
            .order_by('status')
            
        status_counts = {item['status']: item['count'] for item in orders_by_status}

        data = {
            'restaurant_id': restaurant_obj.id,
            'restaurant_name': restaurant_obj.name,
            'total_orders': total_orders,
            'total_menu_items': total_menu_items,
            'orders_by_status': status_counts,
        }
        return Response(data)