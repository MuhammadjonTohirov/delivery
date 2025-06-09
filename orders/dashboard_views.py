from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Count, Sum, Avg, Q
from django.utils.dateparse import parse_date
from datetime import datetime, date
from .models import Order
from .serializers import OrderListSerializer
from restaurants.models import Restaurant
from users.permissions import IsRestaurantOwner
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes


@extend_schema(
    summary="Get dashboard statistics",
    description="Get dashboard statistics including orders count, revenue, and average order price with filters",
    parameters=[
        OpenApiParameter(
            name='restaurant_id',
            type=OpenApiTypes.UUID,
            location=OpenApiParameter.QUERY,
            description='Filter by restaurant ID (optional for admin, required for restaurant owners)',
            required=False
        ),
        OpenApiParameter(
            name='date_from',
            type=OpenApiTypes.DATE,
            location=OpenApiParameter.QUERY,
            description='Start date for filtering (YYYY-MM-DD format)',
            required=False
        ),
        OpenApiParameter(
            name='date_to',
            type=OpenApiTypes.DATE,
            location=OpenApiParameter.QUERY,
            description='End date for filtering (YYYY-MM-DD format)',
            required=False
        ),
        OpenApiParameter(
            name='status',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description='Filter by order status',
            required=False,
            enum=['PLACED', 'CONFIRMED', 'PREPARING', 'READY_FOR_PICKUP', 'PICKED_UP', 'ON_THE_WAY', 'DELIVERED', 'CANCELLED']
        ),
    ],
    responses={
        200: {
            'type': 'object',
            'properties': {
                'orders_count': {'type': 'integer'},
                'revenue': {'type': 'number', 'format': 'decimal'},
                'average_order_price': {'type': 'number', 'format': 'decimal'},
            }
        }
    }
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_statistics(request):
    """
    Get dashboard statistics with filtering options.
    """
    user = request.user
    
    # Build base queryset based on user role
    if user.is_staff:
        # Admin can see all orders
        queryset = Order.objects.all()
    elif user.is_restaurant_owner() and hasattr(user, 'restaurant'):
        # Restaurant owner can only see their own orders
        queryset = Order.objects.filter(restaurant=user.restaurant)
    else:
        return Response(
            {"error": "You don't have permission to view dashboard statistics."},
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Apply filters
    restaurant_id = request.query_params.get('restaurant_id')
    if restaurant_id:
        if user.is_staff:
            # Admin can filter by any restaurant
            queryset = queryset.filter(restaurant_id=restaurant_id)
        elif user.is_restaurant_owner():
            # Restaurant owner can only filter by their own restaurant
            if str(user.restaurant.id) != restaurant_id:
                return Response(
                    {"error": "You can only view statistics for your own restaurant."},
                    status=status.HTTP_403_FORBIDDEN
                )
    
    # Date filtering
    date_from = request.query_params.get('date_from')
    date_to = request.query_params.get('date_to')
    
    if date_from:
        try:
            date_from = parse_date(date_from)
            if date_from:
                queryset = queryset.filter(created_at__date__gte=date_from)
        except ValueError:
            return Response(
                {"error": "Invalid date_from format. Use YYYY-MM-DD."},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    if date_to:
        try:
            date_to = parse_date(date_to)
            if date_to:
                queryset = queryset.filter(created_at__date__lte=date_to)
        except ValueError:
            return Response(
                {"error": "Invalid date_to format. Use YYYY-MM-DD."},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    # Status filtering
    order_status = request.query_params.get('status')
    if order_status:
        valid_statuses = [choice[0] for choice in Order.ORDER_STATUS_CHOICES]
        if order_status not in valid_statuses:
            return Response(
                {"error": f"Invalid status. Valid options: {', '.join(valid_statuses)}"},
                status=status.HTTP_400_BAD_REQUEST
            )
        queryset = queryset.filter(status=order_status)
    
    # Calculate statistics
    stats = queryset.aggregate(
        orders_count=Count('id'),
        revenue=Sum('total_price'),
        average_order_price=Avg('total_price')
    )
    
    # Handle None values
    stats['orders_count'] = stats['orders_count'] or 0
    stats['revenue'] = float(stats['revenue'] or 0)
    stats['average_order_price'] = float(stats['average_order_price'] or 0)
    
    return Response(stats)


@extend_schema(
    summary="Get recent orders for dashboard",
    description="Get recent orders list with filtering and pagination for dashboard",
    parameters=[
        OpenApiParameter(
            name='restaurant_id',
            type=OpenApiTypes.UUID,
            location=OpenApiParameter.QUERY,
            description='Filter by restaurant ID (optional for admin, required for restaurant owners)',
            required=False
        ),
        OpenApiParameter(
            name='date_from',
            type=OpenApiTypes.DATE,
            location=OpenApiParameter.QUERY,
            description='Start date for filtering (YYYY-MM-DD format)',
            required=False
        ),
        OpenApiParameter(
            name='date_to',
            type=OpenApiTypes.DATE,
            location=OpenApiParameter.QUERY,
            description='End date for filtering (YYYY-MM-DD format)',
            required=False
        ),
        OpenApiParameter(
            name='status',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description='Filter by order status',
            required=False,
            enum=['PLACED', 'CONFIRMED', 'PREPARING', 'READY_FOR_PICKUP', 'PICKED_UP', 'ON_THE_WAY', 'DELIVERED', 'CANCELLED']
        ),
        OpenApiParameter(
            name='limit',
            type=OpenApiTypes.INT,
            location=OpenApiParameter.QUERY,
            description='Number of orders to return (default: 10, max: 100)',
            required=False
        ),
        OpenApiParameter(
            name='offset',
            type=OpenApiTypes.INT,
            location=OpenApiParameter.QUERY,
            description='Number of orders to skip (for pagination)',
            required=False
        ),
    ],
    responses={
        200: {
            'type': 'object',
            'properties': {
                'count': {'type': 'integer'},
                'results': {'type': 'array', 'items': {'$ref': '#/components/schemas/OrderList'}},
            }
        }
    }
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_recent_orders(request):
    """
    Get recent orders for dashboard with filtering options.
    """
    user = request.user
    
    # Build base queryset based on user role
    if user.is_staff:
        # Admin can see all orders
        queryset = Order.objects.all()
    elif user.is_restaurant_owner() and hasattr(user, 'restaurant'):
        # Restaurant owner can only see their own orders
        queryset = Order.objects.filter(restaurant=user.restaurant)
    else:
        return Response(
            {"error": "You don't have permission to view dashboard orders."},
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Apply filters (same logic as statistics)
    restaurant_id = request.query_params.get('restaurant_id')
    if restaurant_id:
        if user.is_staff:
            queryset = queryset.filter(restaurant_id=restaurant_id)
        elif user.is_restaurant_owner():
            if str(user.restaurant.id) != restaurant_id:
                return Response(
                    {"error": "You can only view orders for your own restaurant."},
                    status=status.HTTP_403_FORBIDDEN
                )
    
    # Date filtering
    date_from = request.query_params.get('date_from')
    date_to = request.query_params.get('date_to')
    
    if date_from:
        try:
            date_from = parse_date(date_from)
            if date_from:
                queryset = queryset.filter(created_at__date__gte=date_from)
        except ValueError:
            return Response(
                {"error": "Invalid date_from format. Use YYYY-MM-DD."},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    if date_to:
        try:
            date_to = parse_date(date_to)
            if date_to:
                queryset = queryset.filter(created_at__date__lte=date_to)
        except ValueError:
            return Response(
                {"error": "Invalid date_to format. Use YYYY-MM-DD."},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    # Status filtering
    order_status = request.query_params.get('status')
    if order_status:
        valid_statuses = [choice[0] for choice in Order.ORDER_STATUS_CHOICES]
        if order_status not in valid_statuses:
            return Response(
                {"error": f"Invalid status. Valid options: {', '.join(valid_statuses)}"},
                status=status.HTTP_400_BAD_REQUEST
            )
        queryset = queryset.filter(status=order_status)
    
    # Order by most recent first
    queryset = queryset.select_related('customer', 'restaurant').order_by('-created_at')
    
    # Pagination
    try:
        limit = int(request.query_params.get('limit', 10))
        offset = int(request.query_params.get('offset', 0))
        
        # Limit the maximum number of results
        limit = min(limit, 100)
        
        total_count = queryset.count()
        orders = queryset[offset:offset + limit]
        
    except ValueError:
        return Response(
            {"error": "Invalid limit or offset value."},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Serialize the orders
    serializer = OrderListSerializer(orders, many=True)
    
    return Response({
        'count': total_count,
        'results': serializer.data
    })


@extend_schema(
    summary="Get restaurants list for dashboard filter",
    description="Get list of restaurants for dashboard filtering (admin only)",
    responses={
        200: {
            'type': 'array',
            'items': {
                'type': 'object',
                'properties': {
                    'id': {'type': 'string', 'format': 'uuid'},
                    'name': {'type': 'string'},
                }
            }
        }
    }
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_restaurants(request):
    """
    Get list of restaurants for dashboard filtering.
    Only available for admin users.
    """
    user = request.user
    
    if user.is_restaurant_owner():
        restaurants = Restaurant.objects.filter(user=user).values('id', 'name').order_by('name')
        return Response(list(restaurants))
    
    if user.is_staff:  
        restaurants = Restaurant.objects.all().values('id', 'name').order_by('name')
        
        return Response(list(restaurants))

    return Response({"error": "Only admin users can access this endpoint."}, status=status.HTTP_403_FORBIDDEN)