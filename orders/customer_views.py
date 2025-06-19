from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.db.models import Count, Sum, Max, Min, Q
from django.utils.dateparse import parse_date
from django.core.paginator import Paginator
from .models import Order
from users.models import CustomUser
from restaurants.models import Restaurant
from users.permissions import IsRestaurantOwner
from utils.restaurant_helpers import get_restaurant_for_user, filter_restaurants_for_user
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes


@extend_schema(
    summary="Get customers list",
    description="Get list of customers who have ordered from restaurant owner's restaurants",
    parameters=[
        OpenApiParameter(
            name='restaurant',
            type=OpenApiTypes.UUID,
            location=OpenApiParameter.QUERY,
            description='Filter by specific restaurant ID',
            required=False
        ),
        OpenApiParameter(
            name='search',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description='Search by customer name, email, or phone',
            required=False
        ),
        OpenApiParameter(
            name='date_from',
            type=OpenApiTypes.DATE,
            location=OpenApiParameter.QUERY,
            description='Filter customers who ordered from this date',
            required=False
        ),
        OpenApiParameter(
            name='date_to',
            type=OpenApiTypes.DATE,
            location=OpenApiParameter.QUERY,
            description='Filter customers who ordered until this date',
            required=False
        ),
        OpenApiParameter(
            name='page',
            type=OpenApiTypes.INT,
            location=OpenApiParameter.QUERY,
            description='Page number for pagination',
            required=False
        ),
        OpenApiParameter(
            name='page_size',
            type=OpenApiTypes.INT,
            location=OpenApiParameter.QUERY,
            description='Number of customers per page (max 100)',
            required=False
        ),
    ],
    responses={
        200: {
            'type': 'object',
            'properties': {
                'count': {'type': 'integer'},
                'next': {'type': 'string', 'nullable': True},
                'previous': {'type': 'string', 'nullable': True},
                'results': {
                    'type': 'array',
                    'items': {
                        'type': 'object',
                        'properties': {
                            'id': {'type': 'string', 'format': 'uuid'},
                            'name': {'type': 'string'},
                            'email': {'type': 'string'},
                            'phone': {'type': 'string'},
                            'total_orders': {'type': 'integer'},
                            'total_spent': {'type': 'string'},
                            'last_order_date': {'type': 'string', 'format': 'date-time'},
                            'first_order_date': {'type': 'string', 'format': 'date-time'},
                        }
                    }
                }
            }
        }
    }
)
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated, IsRestaurantOwner])
def customers_list(request):
    """
    Get list of customers who have ordered from restaurant owner's restaurants
    """
    user = request.user
    
    # Get the base queryset of orders from user's restaurants
    if user.is_staff or user.is_superuser:
        # Admin users can access all restaurants
        orders_queryset = Order.objects.all()
    else:
        # Regular users can only access their own restaurants
        orders_queryset = Order.objects.filter(restaurant__user=user)
    
    # Apply filters
    restaurant_id = request.query_params.get('restaurant')
    if restaurant_id:
        # Verify the restaurant belongs to the user
        try:
            restaurant = get_restaurant_for_user(restaurant_id, user)
            orders_queryset = orders_queryset.filter(restaurant=restaurant)
        except Restaurant.DoesNotExist:
            return Response(
                {"error": "Restaurant not found or you don't have permission to access it."},
                status=status.HTTP_404_NOT_FOUND
            )
    
    # Date filtering
    date_from = request.query_params.get('date_from')
    date_to = request.query_params.get('date_to')
    
    if date_from:
        try:
            date_from_parsed = parse_date(date_from)
            if date_from_parsed:
                orders_queryset = orders_queryset.filter(created_at__date__gte=date_from_parsed)
        except ValueError:
            return Response(
                {"error": "Invalid date_from format. Use YYYY-MM-DD."},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    if date_to:
        try:
            date_to_parsed = parse_date(date_to)
            if date_to_parsed:
                orders_queryset = orders_queryset.filter(created_at__date__lte=date_to_parsed)
        except ValueError:
            return Response(
                {"error": "Invalid date_to format. Use YYYY-MM-DD."},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    # Aggregate customer data
    customers_data = orders_queryset.values('customer').annotate(
        total_orders=Count('id'),
        total_spent=Sum('total_price'),
        last_order_date=Max('created_at'),
        first_order_date=Min('created_at')
    ).order_by('-last_order_date')
    
    # Get customer details and apply search filter
    search = request.query_params.get('search', '').strip()
    customer_ids = [item['customer'] for item in customers_data]
    
    customers_queryset = CustomUser.objects.filter(id__in=customer_ids)
    
    if search:
        customers_queryset = customers_queryset.filter(
            Q(full_name__icontains=search) |
            Q(email__icontains=search) |
            Q(phone__icontains=search)
        )
    
    # Create lookup dict for aggregated data
    aggregated_lookup = {
        item['customer']: item 
        for item in customers_data
    }
    
    # Build final customer list
    customers_list_data = []
    for customer in customers_queryset:
        agg_data = aggregated_lookup.get(customer.id)
        if agg_data:  # Only include customers with orders
            full_avatar_url = request.build_absolute_uri(customer.avatar.url) if customer.avatar else None

            customers_list_data.append({
                'id': str(customer.id),
                'name': customer.full_name,
                'email': customer.email,
                'phone': customer.phone or '',
                'total_orders': agg_data['total_orders'],
                'total_spent': str(agg_data['total_spent'] or 0),
                'last_order_date': agg_data['last_order_date'],
                'first_order_date': agg_data['first_order_date'],
                'avatar': full_avatar_url
            })
    
    # Sort by last order date (most recent first)
    customers_list_data.sort(key=lambda x: x['last_order_date'], reverse=True)
    
    # Pagination
    page = int(request.query_params.get('page', 1))
    page_size = min(int(request.query_params.get('page_size', 20)), 100)
    
    paginator = Paginator(customers_list_data, page_size)
    
    try:
        page_obj = paginator.get_page(page)
    except Exception:
        return Response(
            {"error": "Invalid page number."},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Build pagination response
    next_page = None
    previous_page = None
    
    if page_obj.has_next():
        next_page = f"{request.build_absolute_uri()}?page={page_obj.next_page_number()}"
        if request.query_params:
            # Preserve existing query parameters
            params = request.query_params.copy()
            params['page'] = page_obj.next_page_number()
            next_page = f"{request.build_absolute_uri().split('?')[0]}?{params.urlencode()}"
    
    if page_obj.has_previous():
        previous_page = f"{request.build_absolute_uri()}?page={page_obj.previous_page_number()}"
        if request.query_params:
            # Preserve existing query parameters
            params = request.query_params.copy()
            params['page'] = page_obj.previous_page_number()
            previous_page = f"{request.build_absolute_uri().split('?')[0]}?{params.urlencode()}"
    
    return Response({
        'count': paginator.count,
        'next': next_page,
        'previous': previous_page,
        'results': list(page_obj)
    })


@extend_schema(
    summary="Get customer summary",
    description="Get detailed summary of a customer including their order history and restaurant breakdown",
    responses={
        200: {
            'type': 'object',
            'properties': {
                'customer': {
                    'type': 'object',
                    'properties': {
                        'id': {'type': 'string', 'format': 'uuid'},
                        'name': {'type': 'string'},
                        'email': {'type': 'string'},
                        'phone': {'type': 'string'},
                    }
                },
                'total_orders': {'type': 'integer'},
                'total_spent': {'type': 'string'},
                'restaurants': {
                    'type': 'array',
                    'items': {
                        'type': 'object',
                        'properties': {
                            'id': {'type': 'string', 'format': 'uuid'},
                            'name': {'type': 'string'},
                            'order_count': {'type': 'integer'}
                        }
                    }
                }
            }
        }
    }
)
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated, IsRestaurantOwner])
def customer_summary(request, customer_id):
    """
    Get detailed summary of a specific customer
    """
    user = request.user
    
    # Verify customer exists and has ordered from user's restaurants
    try:
        customer = CustomUser.objects.get(id=customer_id)
    except CustomUser.DoesNotExist:
        return Response(
            {"error": "Customer not found."},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Get orders from user's restaurants for this customer
    if user.is_staff or user.is_superuser:
        # Admin users can access all orders for the customer
        orders = Order.objects.filter(customer=customer)
    else:
        # Regular users can only access orders from their own restaurants
        orders = Order.objects.filter(
            customer=customer,
            restaurant__user=user
        )
    
    if not orders.exists():
        return Response(
            {"error": "Customer has no orders from your restaurants."},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Calculate totals
    total_orders = orders.count()
    total_spent = orders.aggregate(total=Sum('total_price'))['total'] or 0
    
    # Get restaurant breakdown
    restaurant_data = orders.values('restaurant__id', 'restaurant__name').annotate(
        order_count=Count('id')
    ).order_by('-order_count')
    
    restaurants = [
        {
            'id': str(item['restaurant__id']),
            'name': item['restaurant__name'],
            'order_count': item['order_count']
        }
        for item in restaurant_data
    ]
    # full avatar url
    full_avatar_url = request.build_absolute_uri(customer.avatar.url) if customer.avatar else None
    return Response({
        'customer': {
            'id': str(customer.id),
            'name': customer.full_name,
            'email': customer.email,
            'phone': customer.phone or '',
            'avatar': full_avatar_url
        },
        'total_orders': total_orders,
        'total_spent': str(total_spent),
        'restaurants': restaurants
    })