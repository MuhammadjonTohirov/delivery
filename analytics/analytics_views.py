from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.db.models import Count, Sum, Avg, Q, F
from django.utils.dateparse import parse_date
from django.utils import timezone
from datetime import datetime, timedelta, date
from collections import defaultdict, Counter
from orders.models import Order, OrderItem
from restaurants.models import MenuItem, MenuCategory, Restaurant
from users.models import CustomUser
from users.permissions import IsRestaurantOwner
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes


@extend_schema(
    summary="Get business performance analytics",
    description="Get revenue trends, order volume, and key performance metrics",
    parameters=[
        OpenApiParameter(
            name='restaurant',
            type=OpenApiTypes.UUID,
            location=OpenApiParameter.QUERY,
            description='Filter by specific restaurant ID',
            required=False
        ),
        OpenApiParameter(
            name='period',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description='Time period: today, week, month, quarter, year',
            required=False,
            enum=['today', 'week', 'month', 'quarter', 'year']
        ),
        OpenApiParameter(
            name='date_from',
            type=OpenApiTypes.DATE,
            location=OpenApiParameter.QUERY,
            description='Custom start date (YYYY-MM-DD)',
            required=False
        ),
        OpenApiParameter(
            name='date_to',
            type=OpenApiTypes.DATE,
            location=OpenApiParameter.QUERY,
            description='Custom end date (YYYY-MM-DD)',
            required=False
        ),
    ],
    responses={
        200: {
            'type': 'object',
            'properties': {
                'summary': {
                    'type': 'object',
                    'properties': {
                        'total_revenue': {'type': 'string'},
                        'total_orders': {'type': 'integer'},
                        'average_order_value': {'type': 'string'},
                        'revenue_growth': {'type': 'number'},
                        'orders_growth': {'type': 'number'},
                    }
                },
                'revenue_trends': {
                    'type': 'array',
                    'items': {
                        'type': 'object',
                        'properties': {
                            'date': {'type': 'string'},
                            'revenue': {'type': 'string'},
                            'orders': {'type': 'integer'}
                        }
                    }
                }
            }
        }
    }
)
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated, IsRestaurantOwner])
def business_performance(request):
    """
    Get business performance analytics including revenue trends and key metrics
    """
    user = request.user
    
    # Get date range
    date_from, date_to = get_date_range(request)
    previous_date_from, previous_date_to = get_previous_period(date_from, date_to)
    
    # Base queryset
    orders_queryset = Order.objects.filter(restaurant__user=user)
    
    # Apply restaurant filter
    restaurant_id = request.query_params.get('restaurant')
    if restaurant_id:
        try:
            restaurant = Restaurant.objects.get(id=restaurant_id, user=user)
            orders_queryset = orders_queryset.filter(restaurant=restaurant)
        except Restaurant.DoesNotExist:
            return Response(
                {"error": "Restaurant not found or you don't have permission to access it."},
                status=status.HTTP_404_NOT_FOUND
            )
    
    # Current period data
    current_orders = orders_queryset.filter(
        created_at__date__gte=date_from,
        created_at__date__lte=date_to,
        status__in=['DELIVERED', 'PICKED_UP']  # Only completed orders
    )
    
    # Previous period data for comparison
    previous_orders = orders_queryset.filter(
        created_at__date__gte=previous_date_from,
        created_at__date__lte=previous_date_to,
        status__in=['DELIVERED', 'PICKED_UP']
    )
    
    # Calculate current period metrics
    current_metrics = current_orders.aggregate(
        total_revenue=Sum('total_price'),
        total_orders=Count('id'),
        average_order_value=Avg('total_price')
    )
    
    # Calculate previous period metrics
    previous_metrics = previous_orders.aggregate(
        total_revenue=Sum('total_price'),
        total_orders=Count('id'),
        average_order_value=Avg('total_price')
    )
    
    # Calculate growth rates
    revenue_growth = calculate_growth_rate(
        current_metrics['total_revenue'] or 0,
        previous_metrics['total_revenue'] or 0
    )
    
    orders_growth = calculate_growth_rate(
        current_metrics['total_orders'] or 0,
        previous_metrics['total_orders'] or 0
    )
    
    # Generate daily revenue trends
    revenue_trends = []
    current_date = date_from
    while current_date <= date_to:
        daily_data = current_orders.filter(
            created_at__date=current_date
        ).aggregate(
            revenue=Sum('total_price'),
            orders=Count('id')
        )
        
        revenue_trends.append({
            'date': current_date.isoformat(),
            'revenue': str(daily_data['revenue'] or 0),
            'orders': daily_data['orders'] or 0
        })
        
        current_date += timedelta(days=1)
    
    return Response({
        'summary': {
            'total_revenue': str(current_metrics['total_revenue'] or 0),
            'total_orders': current_metrics['total_orders'] or 0,
            'average_order_value': str(current_metrics['average_order_value'] or 0),
            'revenue_growth': revenue_growth,
            'orders_growth': orders_growth,
        },
        'revenue_trends': revenue_trends
    })


@extend_schema(
    summary="Get menu performance analytics",
    description="Get top selling items, category performance, and menu insights",
    parameters=[
        OpenApiParameter(
            name='restaurant',
            type=OpenApiTypes.UUID,
            location=OpenApiParameter.QUERY,
            description='Filter by specific restaurant ID',
            required=False
        ),
        OpenApiParameter(
            name='period',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description='Time period: today, week, month, quarter, year',
            required=False,
            enum=['today', 'week', 'month', 'quarter', 'year']
        ),
        OpenApiParameter(
            name='limit',
            type=OpenApiTypes.INT,
            location=OpenApiParameter.QUERY,
            description='Number of top items to return (default: 10)',
            required=False
        ),
    ],
)
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated, IsRestaurantOwner])
def menu_performance(request):
    """
    Get menu performance analytics including top items and category breakdown
    """
    user = request.user
    limit = int(request.query_params.get('limit', 10))
    
    # Get date range
    date_from, date_to = get_date_range(request)
    
    # Base queryset
    order_items_queryset = OrderItem.objects.filter(
        order__restaurant__user=user,
        order__created_at__date__gte=date_from,
        order__created_at__date__lte=date_to,
        order__status__in=['DELIVERED', 'PICKED_UP']
    )
    
    # Apply restaurant filter
    restaurant_id = request.query_params.get('restaurant')
    if restaurant_id:
        try:
            restaurant = Restaurant.objects.get(id=restaurant_id, user=user)
            order_items_queryset = order_items_queryset.filter(order__restaurant=restaurant)
        except Restaurant.DoesNotExist:
            return Response(
                {"error": "Restaurant not found or you don't have permission to access it."},
                status=status.HTTP_404_NOT_FOUND
            )
    
    # Top selling items by quantity
    top_items_by_quantity = order_items_queryset.values(
        'menu_item__id',
        'menu_item__name',
        'menu_item__price',
        'menu_item__currency'
    ).annotate(
        total_quantity=Sum('quantity'),
        total_revenue=Sum(F('quantity') * F('unit_price'))
    ).order_by('-total_quantity')[:limit]
    
    # Top selling items by revenue
    top_items_by_revenue = order_items_queryset.values(
        'menu_item__id',
        'menu_item__name',
        'menu_item__price',
        'menu_item__currency'
    ).annotate(
        total_quantity=Sum('quantity'),
        total_revenue=Sum(F('quantity') * F('unit_price'))
    ).order_by('-total_revenue')[:limit]
    
    # Category performance
    category_performance = order_items_queryset.values(
        'menu_item__category__id',
        'menu_item__category__name'
    ).annotate(
        total_quantity=Sum('quantity'),
        total_revenue=Sum(F('quantity') * F('unit_price')),
        unique_items=Count('menu_item__id', distinct=True)
    ).order_by('-total_revenue')
    
    # Format response
    top_by_quantity = [
        {
            'item_id': str(item['menu_item__id']),
            'name': item['menu_item__name'],
            'price': str(item['menu_item__price']),
            'currency': item['menu_item__currency'],
            'total_quantity': item['total_quantity'],
            'total_revenue': str(item['total_revenue'])
        }
        for item in top_items_by_quantity
    ]
    
    top_by_revenue = [
        {
            'item_id': str(item['menu_item__id']),
            'name': item['menu_item__name'],
            'price': str(item['menu_item__price']),
            'currency': item['menu_item__currency'],
            'total_quantity': item['total_quantity'],
            'total_revenue': str(item['total_revenue'])
        }
        for item in top_items_by_revenue
    ]
    
    categories = [
        {
            'category_id': str(item['menu_item__category__id']) if item['menu_item__category__id'] else None,
            'name': item['menu_item__category__name'] or 'Uncategorized',
            'total_quantity': item['total_quantity'],
            'total_revenue': str(item['total_revenue']),
            'unique_items': item['unique_items']
        }
        for item in category_performance
    ]
    
    return Response({
        'top_items_by_quantity': top_by_quantity,
        'top_items_by_revenue': top_by_revenue,
        'category_performance': categories
    })


@extend_schema(
    summary="Get customer analytics",
    description="Get customer acquisition, retention, and lifetime value metrics",
    parameters=[
        OpenApiParameter(
            name='restaurant',
            type=OpenApiTypes.UUID,
            location=OpenApiParameter.QUERY,
            description='Filter by specific restaurant ID',
            required=False
        ),
        OpenApiParameter(
            name='period',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description='Time period: today, week, month, quarter, year',
            required=False,
            enum=['today', 'week', 'month', 'quarter', 'year']
        ),
    ],
)
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated, IsRestaurantOwner])
def customer_analytics(request):
    """
    Get customer analytics including acquisition, retention, and lifetime value
    """
    user = request.user
    
    # Get date range
    date_from, date_to = get_date_range(request)
    previous_date_from, previous_date_to = get_previous_period(date_from, date_to)
    
    # Base queryset
    orders_queryset = Order.objects.filter(restaurant__user=user)
    
    # Apply restaurant filter
    restaurant_id = request.query_params.get('restaurant')
    if restaurant_id:
        try:
            restaurant = Restaurant.objects.get(id=restaurant_id, user=user)
            orders_queryset = orders_queryset.filter(restaurant=restaurant)
        except Restaurant.DoesNotExist:
            return Response(
                {"error": "Restaurant not found or you don't have permission to access it."},
                status=status.HTTP_404_NOT_FOUND
            )
    
    # Current period orders
    current_orders = orders_queryset.filter(
        created_at__date__gte=date_from,
        created_at__date__lte=date_to
    )
    
    # Previous period orders
    previous_orders = orders_queryset.filter(
        created_at__date__gte=previous_date_from,
        created_at__date__lte=previous_date_to
    )
    
    # Customer acquisition - new customers in current period
    new_customers_current = get_new_customers(orders_queryset, date_from, date_to)
    new_customers_previous = get_new_customers(orders_queryset, previous_date_from, previous_date_to)
    
    # Total unique customers in current period
    total_customers_current = current_orders.values('customer').distinct().count()
    total_customers_previous = previous_orders.values('customer').distinct().count()
    
    # Customer retention - customers who ordered in both current and previous periods
    current_customer_ids = set(current_orders.values_list('customer', flat=True).distinct())
    previous_customer_ids = set(previous_orders.values_list('customer', flat=True).distinct())
    returning_customers = len(current_customer_ids.intersection(previous_customer_ids))
    
    retention_rate = (returning_customers / total_customers_previous * 100) if total_customers_previous > 0 else 0
    
    # Customer lifetime value
    customer_ltv = calculate_customer_ltv(orders_queryset, date_from, date_to)
    
    # Daily acquisition trends
    acquisition_trends = []
    current_date = date_from
    while current_date <= date_to:
        daily_new_customers = get_new_customers(orders_queryset, current_date, current_date)
        acquisition_trends.append({
            'date': current_date.isoformat(),
            'new_customers': daily_new_customers
        })
        current_date += timedelta(days=1)
    
    # Calculate growth rates
    acquisition_growth = calculate_growth_rate(new_customers_current, new_customers_previous)
    
    return Response({
        'summary': {
            'new_customers': new_customers_current,
            'total_customers': total_customers_current,
            'retention_rate': round(retention_rate, 2),
            'average_ltv': str(customer_ltv),
            'acquisition_growth': acquisition_growth,
        },
        'acquisition_trends': acquisition_trends
    })


# Helper functions
def get_date_range(request):
    """Get date range based on period parameter or custom dates"""
    period = request.query_params.get('period', 'month')
    date_from_param = request.query_params.get('date_from')
    date_to_param = request.query_params.get('date_to')
    
    if date_from_param and date_to_param:
        date_from = parse_date(date_from_param)
        date_to = parse_date(date_to_param)
    else:
        today = timezone.now().date()
        
        if period == 'today':
            date_from = date_to = today
        elif period == 'week':
            date_from = today - timedelta(days=today.weekday())
            date_to = date_from + timedelta(days=6)
        elif period == 'month':
            date_from = today.replace(day=1)
            if date_from.month == 12:
                date_to = date_from.replace(year=date_from.year + 1, month=1) - timedelta(days=1)
            else:
                date_to = date_from.replace(month=date_from.month + 1) - timedelta(days=1)
        elif period == 'quarter':
            quarter = (today.month - 1) // 3 + 1
            date_from = today.replace(month=(quarter - 1) * 3 + 1, day=1)
            if quarter == 4:
                date_to = date_from.replace(year=date_from.year + 1, month=1) - timedelta(days=1)
            else:
                date_to = date_from.replace(month=quarter * 3 + 1) - timedelta(days=1)
        elif period == 'year':
            date_from = today.replace(month=1, day=1)
            date_to = today.replace(month=12, day=31)
        else:
            # Default to current month
            date_from = today.replace(day=1)
            if date_from.month == 12:
                date_to = date_from.replace(year=date_from.year + 1, month=1) - timedelta(days=1)
            else:
                date_to = date_from.replace(month=date_from.month + 1) - timedelta(days=1)
    
    return date_from, date_to


def get_previous_period(date_from, date_to):
    """Get the previous period dates for comparison"""
    period_length = (date_to - date_from).days + 1
    previous_date_to = date_from - timedelta(days=1)
    previous_date_from = previous_date_to - timedelta(days=period_length - 1)
    return previous_date_from, previous_date_to


def calculate_growth_rate(current, previous):
    """Calculate growth rate percentage"""
    if previous == 0:
        return 100.0 if current > 0 else 0.0
    return round(((current - previous) / previous) * 100, 2)


def get_new_customers(orders_queryset, date_from, date_to):
    """Get count of new customers in the given period"""
    # Get customers who placed their first order in this period
    customers_in_period = orders_queryset.filter(
        created_at__date__gte=date_from,
        created_at__date__lte=date_to
    ).values_list('customer', flat=True).distinct()
    
    new_customers_count = 0
    for customer_id in customers_in_period:
        first_order = orders_queryset.filter(customer=customer_id).order_by('created_at').first()
        if first_order and date_from <= first_order.created_at.date() <= date_to:
            new_customers_count += 1
    
    return new_customers_count


def calculate_customer_ltv(orders_queryset, date_from, date_to):
    """Calculate average customer lifetime value"""
    # Get all customers who ordered in the period
    customer_data = orders_queryset.filter(
        created_at__date__gte=date_from,
        created_at__date__lte=date_to,
        status__in=['DELIVERED', 'PICKED_UP']
    ).values('customer').annotate(
        total_spent=Sum('total_price'),
        order_count=Count('id')
    )
    
    if not customer_data:
        return 0
    
    total_ltv = sum(item['total_spent'] for item in customer_data)
    customer_count = len(customer_data)
    
    return total_ltv / customer_count if customer_count > 0 else 0