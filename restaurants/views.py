from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import Restaurant, MenuCategory, MenuItem, RestaurantReview
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
        if hasattr(request.user, 'restaurant'):
            return obj.user == request.user or request.user.is_staff
        return request.user.is_staff


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
    queryset = Restaurant.objects.all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_open']
    search_fields = ['name', 'address']
    ordering_fields = ['name', 'created_at']
    
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
    
    def get_queryset(self):
        return MenuCategory.objects.all()
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [permissions.IsAuthenticated, IsRestaurantOwner]
        else:
            permission_classes = [permissions.AllowAny]
        return [permission() for permission in permission_classes]
    
    def perform_create(self, serializer):
        # Automatically set the restaurant to the user's restaurant
        if self.request.user.role == 'RESTAURANT' and hasattr(self.request.user, 'restaurant'):
            serializer.save(restaurant=self.request.user.restaurant)
        else:
            serializer.save()


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
        # Automatically set the restaurant to the user's restaurant
        if self.request.user.role == 'RESTAURANT' and hasattr(self.request.user, 'restaurant'):
            serializer.save(restaurant=self.request.user.restaurant)
        else:
            serializer.save()


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