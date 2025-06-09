from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, ValidationError
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count, Avg, Q
from django.shortcuts import get_object_or_404
import uuid

from .models import Restaurant, MenuCategory, MenuItem, RestaurantReview
from orders.models import Order
from .serializers import (
    RestaurantSerializer, 
    RestaurantListSerializer,
    MenuCategorySerializer, 
    MenuCategoryWithItemsSerializer,
    MenuItemSerializer, 
    RestaurantReviewSerializer
)
from .permissions import (
    IsRestaurantOwnerOrAdmin,
    IsRestaurantOwnerOnly,
    CanModifyRestaurantData,
    IsMenuCategoryOwner,
    IsMenuItemOwner
)
from users.permissions import IsCustomer, IsOwnerOrAdmin
from drf_spectacular.utils import extend_schema, extend_schema_view


@extend_schema_view(
    list=extend_schema(summary="List all restaurants", description="Get a list of all active restaurants", tags=['Core Business Operations']),
    retrieve=extend_schema(summary="Get restaurant details", description="Retrieve detailed information about a specific restaurant", tags=['Core Business Operations']),
    create=extend_schema(summary="Create restaurant", description="Create a new restaurant (Restaurant user only)", tags=['Core Business Operations']),
    update=extend_schema(summary="Update restaurant", description="Update restaurant details (Restaurant owner only)", tags=['Core Business Operations']),
    partial_update=extend_schema(summary="Partial update restaurant", description="Partially update restaurant details (Restaurant owner only)", tags=['Core Business Operations']),
)
class RestaurantViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Restaurant model.
    """
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_open']
    search_fields = ['name', 'address', 'description']
    ordering_fields = ['name', 'created_at']
    tags = ['Core Business Operations']

    def get_queryset(self):
        queryset = Restaurant.objects.all()
        
        if self.request.user.is_restaurant_owner():
            # If the user is a restaurant owner, filter to only their restaurant
            queryset = queryset.filter(user=self.request.user)
        elif self.request.user.is_superuser or self.request.user.is_staff:
            # If the user is authenticated but not an owner, show all open restaurants
            queryset = queryset.filter(is_open=True)
        
        # Annotate with average rating for all operations
        queryset = queryset.annotate(average_rating_annotated=Avg('reviews__rating'))
        
        return queryset
    
    def get_serializer_class(self):
        if self.action == 'list':
            return RestaurantListSerializer
        return RestaurantSerializer
    
    def get_permissions(self):
        if self.action in ['update', 'partial_update', 'destroy']:
            permission_classes = [permissions.IsAuthenticated, IsRestaurantOwnerOrAdmin]
        elif self.action == 'create':
            permission_classes = [permissions.IsAuthenticated, IsRestaurantOwnerOnly]
        else:
            permission_classes = [permissions.AllowAny]
        return [permission() for permission in permission_classes]
    
    def perform_create(self, serializer):
        """
        Create a restaurant and associate it with the current user.
        """
        user = self.request.user
        
        # Check if user already has a restaurant
        if hasattr(user, 'restaurant'):
            raise ValidationError({"detail": "User already has a restaurant."})
        
        serializer.save(user=user)

    @extend_schema(
        summary="Get restaurant menu",
        description="Get the full menu (categories and items) for a specific restaurant"
    )
    @action(detail=True, methods=['get'])
    def menu(self, request, pk=None):
        restaurant = self.get_object()
        # Get categories that have items in this restaurant
        categories = MenuCategory.objects.filter(
            items__restaurant=restaurant,
            is_active=True
        ).distinct().prefetch_related('items').order_by('order', 'name')
        
        serializer = MenuCategoryWithItemsSerializer(
            categories,
            many=True,
            context={'restaurant': restaurant}
        )
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
    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated, IsRestaurantOwnerOnly])
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
        except AttributeError:
            return Response(
                {"detail": "No restaurant associated with this user account."}, 
                status=status.HTTP_404_NOT_FOUND
            )

    @extend_schema(
        summary="Search restaurants and menu items",
        description="Advanced search across restaurants and menu items with filters"
    )
    @action(detail=False, methods=['get'])
    def search(self, request):
        query = request.query_params.get('q', '')
        min_rating = request.query_params.get('min_rating')
        is_open = request.query_params.get('is_open')
        
        restaurants = self.get_queryset()
        
        # Text search in name and description
        if query:
            restaurants = restaurants.filter(
                Q(name__icontains=query) | Q(description__icontains=query)
            )
        
        # Filter by minimum rating
        if min_rating:
            restaurants = restaurants.filter(average_rating_annotated__gte=float(min_rating))
        
        # Filter by open status
        if is_open:
            restaurants = restaurants.filter(is_open=is_open.lower() == 'true')
        
        # Search in menu items as well
        if query:
            menu_items = MenuItem.objects.filter(
                is_available=True
            ).filter(
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
    Categories are now global and can be used by all restaurants.
    """
    serializer_class = MenuCategorySerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['is_active']
    ordering_fields = ['order', 'name', 'created_at']
    
    def get_queryset(self):
        return MenuCategory.objects.all()
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [permissions.IsAuthenticated, IsMenuCategoryOwner]
        else:
            permission_classes = [permissions.AllowAny]
        return [permission() for permission in permission_classes]
    
    def perform_create(self, serializer):
        # Only staff can create global categories
        if not self.request.user.is_staff:
            raise PermissionDenied("Only administrators can create menu categories.")
        serializer.save()
    
    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def used_by_restaurant(self, request):
        """Get categories that have items in the current user's restaurant"""
        if not request.user.is_restaurant_owner() or not hasattr(request.user, 'restaurant'):
            return Response(
                {"detail": "No restaurant associated with this user account."},
                status=status.HTTP_404_NOT_FOUND
            )
        
        restaurant = request.user.restaurant
        categories = MenuCategory.objects.filter(
            items__restaurant=restaurant
        ).distinct().order_by('order', 'name')
        
        # Add restaurant context for the serializer
        serializer = self.get_serializer(categories, many=True, context={'restaurant': restaurant})
        return Response(serializer.data)


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
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['restaurant', 'category', 'is_available', 'is_featured']
    search_fields = ['name', 'description', 'ingredients', 'allergens']
    ordering_fields = ['name', 'price', 'created_at']
    
    def get_queryset(self):
        return MenuItem.objects.all()
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [permissions.IsAuthenticated, IsMenuItemOwner]
        else:
            permission_classes = [permissions.AllowAny]
        return [permission() for permission in permission_classes]
    
    def perform_create(self, serializer):
        if self.request.user.is_staff:
            # Admin can create for any restaurant specified in payload
            if 'restaurant' not in serializer.validated_data:
                raise ValidationError({"restaurant": "Restaurant must be specified for admin creation."})
            serializer.save()
        elif self.request.user.is_restaurant_owner() and hasattr(self.request.user, 'restaurant'):
            # Validate that category belongs to the restaurant if provided
            category = serializer.validated_data.get('category')
            if category and category.restaurant != self.request.user.restaurant:
                raise ValidationError({"category": "Category must belong to your restaurant."})
                
            serializer.save(restaurant=self.request.user.restaurant)
        else:
            raise PermissionDenied("You do not have permission to create this resource.")
    
    def perform_update(self, serializer):
        # Validate that category belongs to the restaurant if provided
        category = serializer.validated_data.get('category')
        if category and not self.request.user.is_staff:
            restaurant = self.request.user.restaurant
            if category.restaurant != restaurant:
                raise ValidationError({"category": "Category must belong to your restaurant."})
        
        serializer.save()
    
    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated, IsRestaurantOwnerOnly])
    def my_items(self, request):
        """Get all menu items for the current restaurant owner"""
        try:
            restaurant = request.user.restaurant
            items = MenuItem.objects.filter(restaurant=restaurant)
            
            # Apply filters from query params
            category_id = request.query_params.get('category')
            if category_id:
                items = items.filter(category_id=category_id)
                
            is_available = request.query_params.get('is_available')
            if is_available is not None:
                items = items.filter(is_available=is_available.lower() == 'true')
                
            is_featured = request.query_params.get('is_featured')
            if is_featured is not None:
                items = items.filter(is_featured=is_featured.lower() == 'true')
            
            serializer = self.get_serializer(items, many=True)
            return Response(serializer.data)
        except (Restaurant.DoesNotExist, AttributeError):
            return Response(
                {"detail": "No restaurant associated with this user account."}, 
                status=status.HTTP_404_NOT_FOUND
            )


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
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['restaurant', 'user', 'rating']
    ordering_fields = ['created_at', 'rating']
    
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
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class RestaurantStatisticsViewSet(viewsets.ViewSet):
    """
    ViewSet for restaurant statistics.
    """
    permission_classes = [permissions.IsAuthenticated, IsRestaurantOwnerOrAdmin]
    
    @extend_schema(
        summary="Get restaurant statistics",
        description="Get basic statistics for a restaurant. Restaurant owners can only access their own statistics."
    )
    @action(detail=True, methods=['get'])
    def get(self, request, pk=None):
        # Convert string UUID to UUID object for comparison
        restaurant_id = uuid.UUID(pk)
        
        # For restaurant owners, ensure they can only access their own restaurant
        if not request.user.is_staff and hasattr(request.user, 'restaurant'):
            if request.user.restaurant.id != restaurant_id:
                raise PermissionDenied("You can only access statistics for your own restaurant.")
        
        # Get the restaurant
        restaurant = get_object_or_404(Restaurant, id=restaurant_id)
        
        # Calculate statistics
        total_orders = Order.objects.filter(restaurant=restaurant).count()
        total_menu_items = MenuItem.objects.filter(restaurant=restaurant).count()
        total_categories = MenuCategory.objects.filter(items__restaurant=restaurant).distinct().count()
        
        orders_by_status = Order.objects.filter(restaurant=restaurant)\
            .values('status')\
            .annotate(count=Count('status'))\
            .order_by('status')
            
        status_counts = {item['status']: item['count'] for item in orders_by_status}
        
        # Get top menu items
        top_items = MenuItem.objects.filter(restaurant=restaurant)\
            .annotate(order_count=Count('order_items'))\
            .order_by('-order_count')[:5]
            
        top_items_data = [
            {
                'id': item.id,
                'name': item.name,
                'order_count': item.order_count
            }
            for item in top_items
        ]

        data = {
            'restaurant_id': restaurant.id,
            'restaurant_name': restaurant.name,
            'total_orders': total_orders,
            'total_menu_items': total_menu_items,
            'total_categories': total_categories,
            'orders_by_status': status_counts,
            'top_items': top_items_data
        }
        
        return Response(data)