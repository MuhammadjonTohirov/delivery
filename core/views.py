"""
Core views including global search functionality.
"""
from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from django.db.models import Q
from django.core.paginator import Paginator

from restaurants.models import Restaurant, MenuItem, MenuCategory
from orders.models import Order
from users.models import CustomUser
from restaurants.serializers import RestaurantListSerializer, MenuItemSerializer
from orders.serializers import OrderListSerializer
from users.serializers import CustomerSerializer


@extend_schema(
    summary="Global search across restaurants and menu items",
    description="Search across restaurants, menu items, and categories",
    parameters=[
        OpenApiParameter(
            name='q',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description='Search query',
            required=True
        ),
        OpenApiParameter(
            name='type',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description='Search type: all, restaurants, menu_items, categories',
            required=False,
            enum=['all', 'restaurants', 'menu_items', 'categories']
        ),
        OpenApiParameter(
            name='limit',
            type=OpenApiTypes.INT,
            location=OpenApiParameter.QUERY,
            description='Number of results per category (default: 5)',
            required=False
        ),
    ],
    responses={
        200: {
            'type': 'object',
            'properties': {
                'query': {'type': 'string'},
                'total_results': {'type': 'integer'},
                'restaurants': {'type': 'array'},
                'menu_items': {'type': 'array'},
                'categories': {'type': 'array'},
            }
        }
    }
)
@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def global_search(request):
    """
    Global search endpoint for restaurants, menu items, and categories
    """
    query = request.query_params.get('q', '').strip()
    search_type = request.query_params.get('type', 'all')
    limit = int(request.query_params.get('limit', 5))
    
    if not query:
        return Response({
            'error': 'Search query is required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    results = {
        'query': query,
        'total_results': 0,
        'restaurants': [],
        'menu_items': [],
        'categories': [],
    }
    
    # Search restaurants
    if search_type in ['all', 'restaurants']:
        restaurants = Restaurant.objects.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(address__icontains=query)
        ).filter(is_active=True)[:limit]
        
        results['restaurants'] = RestaurantListSerializer(restaurants, many=True).data
        results['total_results'] += restaurants.count()
    
    # Search menu items
    if search_type in ['all', 'menu_items']:
        menu_items = MenuItem.objects.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(ingredients__icontains=query) |
            Q(category__name__icontains=query)
        ).filter(
            is_available=True,
            restaurant__is_active=True
        ).select_related('restaurant', 'category')[:limit]
        
        results['menu_items'] = MenuItemSerializer(menu_items, many=True).data
        results['total_results'] += menu_items.count()
    
    # Search categories
    if search_type in ['all', 'categories']:
        categories = MenuCategory.objects.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query)
        )[:limit]
        
        category_data = []
        for category in categories:
            # Get some menu items from this category
            sample_items = MenuItem.objects.filter(
                category=category,
                is_available=True,
                restaurant__is_active=True
            )[:3]
            
            category_data.append({
                'id': str(category.id),
                'name': category.name,
                'description': category.description,
                'image': category.image.url if category.image else None,
                'item_count': MenuItem.objects.filter(
                    category=category,
                    is_available=True,
                    restaurant__is_active=True
                ).count(),
                'sample_items': MenuItemSerializer(sample_items, many=True).data
            })
        
        results['categories'] = category_data
        results['total_results'] += len(category_data)
    
    return Response(results)


@extend_schema(
    summary="Get search suggestions",
    description="Get autocomplete suggestions for search queries",
    parameters=[
        OpenApiParameter(
            name='q',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description='Partial search query',
            required=True
        ),
        OpenApiParameter(
            name='limit',
            type=OpenApiTypes.INT,
            location=OpenApiParameter.QUERY,
            description='Number of suggestions (default: 8)',
            required=False
        ),
    ],
    responses={
        200: {
            'type': 'object',
            'properties': {
                'suggestions': {
                    'type': 'array',
                    'items': {
                        'type': 'object',
                        'properties': {
                            'text': {'type': 'string'},
                            'type': {'type': 'string'},
                            'id': {'type': 'string'},
                            'subtitle': {'type': 'string'},
                        }
                    }
                }
            }
        }
    }
)
@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def search_suggestions(request):
    """
    Get autocomplete suggestions for search queries
    """
    query = request.query_params.get('q', '').strip()
    limit = int(request.query_params.get('limit', 8))
    
    if len(query) < 2:
        return Response({'suggestions': []})
    
    suggestions = []
    
    # Restaurant name suggestions
    restaurants = Restaurant.objects.filter(
        name__icontains=query,
        is_active=True
    )[:3]
    
    for restaurant in restaurants:
        suggestions.append({
            'text': restaurant.name,
            'type': 'restaurant',
            'id': str(restaurant.id),
            'subtitle': restaurant.address or 'Restaurant'
        })
    
    # Menu item suggestions
    menu_items = MenuItem.objects.filter(
        Q(name__icontains=query),
        is_available=True,
        restaurant__is_active=True
    ).select_related('restaurant')[:5]
    
    for item in menu_items:
        suggestions.append({
            'text': item.name,
            'type': 'menu_item',
            'id': str(item.id),
            'subtitle': f"at {item.restaurant.name}"
        })
    
    # Category suggestions
    categories = MenuCategory.objects.filter(
        name__icontains=query
    )[:2]
    
    for category in categories:
        item_count = MenuItem.objects.filter(
            category=category,
            is_available=True,
            restaurant__is_active=True
        ).count()
        
        suggestions.append({
            'text': category.name,
            'type': 'category',
            'id': str(category.id),
            'subtitle': f"{item_count} items"
        })
    
    # Limit total suggestions
    suggestions = suggestions[:limit]
    
    return Response({'suggestions': suggestions})
