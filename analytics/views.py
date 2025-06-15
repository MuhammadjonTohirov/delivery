from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Count, Sum, Avg, Q, F
from django.utils import timezone
from datetime import datetime, timedelta, date
from django.db.models.functions import TruncDate, TruncHour, TruncWeek, TruncMonth

from .models import AnalyticsEvent, DashboardStats, RevenueMetrics, CustomerInsights, PopularMenuItems
from .serializers import (
    AnalyticsEventSerializer, DashboardStatsSerializer, RevenueMetricsSerializer,
    CustomerInsightsSerializer, PopularMenuItemsSerializer, RestaurantDashboardSerializer,
    PlatformDashboardSerializer, DateRangeSerializer
)
from users.permissions import IsRestaurantOwner, IsAdminUser
from orders.models import Order
from restaurants.models import Restaurant, MenuItem, RestaurantReview
from users.models import CustomUser, DriverProfile
from drf_spectacular.utils import extend_schema, extend_schema_view


class AnalyticsPermission(permissions.BasePermission):
    """
    Custom permission for analytics:
    - Restaurant owners can view their own analytics
    - Admins can view all analytics
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        if request.user.is_staff:
            return True
        
        if request.user.is_restaurant_owner():
            if hasattr(obj, 'restaurant'):
                return obj.restaurant and hasattr(request.user, 'restaurants') and obj.restaurant == request.user.restaurants.first()
        
        return False


@extend_schema_view(
    list=extend_schema(summary="List analytics events", description="List analytics events with filtering", tags=['Communication & Analytics']),
    create=extend_schema(summary="Create analytics event", description="Create a new analytics event", tags=['Communication & Analytics']),
)
class AnalyticsEventViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing analytics events
    """
    serializer_class = AnalyticsEventSerializer
    tags = ['Communication & Analytics']
    permission_classes = [AnalyticsPermission]
    
    def get_queryset(self):
        # Handle schema generation case
        if getattr(self, 'swagger_fake_view', False):
            return AnalyticsEvent.objects.none()
            
        user = self.request.user
        
        if user.is_staff:
            return AnalyticsEvent.objects.all()
        
        if user.is_restaurant_owner() and hasattr(user, 'restaurant'):
            return AnalyticsEvent.objects.filter(restaurant=user.restaurants.first())
        
        return AnalyticsEvent.objects.none()


class RestaurantAnalyticsViewSet(viewsets.ViewSet):
    """
    ViewSet for restaurant-specific analytics and dashboard data
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = RestaurantDashboardSerializer
    
    def get_date_range(self, period='month'):
        """
        Get date range based on period
        """
        end_date = timezone.now().date()
        
        if period == 'today':
            start_date = end_date
        elif period == 'week':
            start_date = end_date - timedelta(days=7)
        elif period == 'month':
            start_date = end_date - timedelta(days=30)
        elif period == 'quarter':
            start_date = end_date - timedelta(days=90)
        elif period == 'year':
            start_date = end_date - timedelta(days=365)
        else:
            start_date = end_date - timedelta(days=30)  # default to month
        
        return start_date, end_date
    
    @extend_schema(
        summary="Get restaurant dashboard analytics",
        description="Get comprehensive analytics data for restaurant dashboard"
    )
    @action(detail=False, methods=['get'])
    def dashboard(self, request):
        """
        Get comprehensive dashboard analytics for a restaurant
        """
        user = request.user
        restaurant_id = request.query_params.get('restaurant_id')
        period = request.query_params.get('period', 'month')
        
        # Determine which restaurant to analyze
        if user.is_staff and restaurant_id:
            try:
                restaurant = Restaurant.objects.get(id=restaurant_id)
            except Restaurant.DoesNotExist:
                return Response(
                    {"error": "Restaurant not found"},
                    status=status.HTTP_404_NOT_FOUND
                )
        elif user.is_restaurant_owner() and hasattr(user, 'restaurant'):
            restaurant = user.restaurants.first()
        else:
            return Response(
                {"error": "No restaurant specified or accessible"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        start_date, end_date = self.get_date_range(period)
        
        # Calculate comprehensive analytics
        analytics_data = self.calculate_restaurant_analytics(restaurant, start_date, end_date)
        
        serializer = RestaurantDashboardSerializer(analytics_data)
        return Response(serializer.data)
    
    def calculate_restaurant_analytics(self, restaurant, start_date, end_date):
        """
        Calculate comprehensive analytics for a restaurant
        """
        # Base order queryset for the period
        orders_qs = Order.objects.filter(
            restaurant=restaurant,
            created_at__date__gte=start_date,
            created_at__date__lte=end_date
        )
        
        # Basic stats
        total_orders = orders_qs.count()
        total_revenue = orders_qs.aggregate(Sum('total_price'))['total_price__sum'] or 0
        
        # Order status breakdown
        orders_by_status = orders_qs.values('status').annotate(count=Count('id'))
        status_dict = {item['status']: item['count'] for item in orders_by_status}
        
        # Customer metrics
        unique_customers = orders_qs.values('customer').distinct().count()
        
        # Get previous period for comparison
        period_days = (end_date - start_date).days
        prev_start = start_date - timedelta(days=period_days)
        prev_end = start_date
        
        prev_orders = Order.objects.filter(
            restaurant=restaurant,
            created_at__date__gte=prev_start,
            created_at__date__lt=prev_end
        )
        
        prev_revenue = prev_orders.aggregate(Sum('total_price'))['total_price__sum'] or 0
        prev_customers = prev_orders.values('customer').distinct().count()
        
        # Calculate growth percentages
        revenue_growth = None
        if prev_revenue > 0:
            revenue_growth = ((total_revenue - prev_revenue) / prev_revenue) * 100
        
        customer_growth = None
        if prev_customers > 0:
            customer_growth = ((unique_customers - prev_customers) / prev_customers) * 100
        
        # Time series data
        daily_orders = self.get_daily_orders(restaurant, start_date, end_date)
        weekly_orders = self.get_weekly_orders(restaurant, start_date, end_date)
        monthly_revenue = self.get_monthly_revenue(restaurant, start_date, end_date)
        
        # Popular items
        popular_items = self.get_popular_items(restaurant, start_date, end_date)
        
        # Average rating
        avg_rating = RestaurantReview.objects.filter(restaurant=restaurant).aggregate(
            Avg('rating')
        )['rating__avg']
        
        # Performance metrics (mock data for now - would need to be calculated from order timestamps)
        avg_prep_time = 25  # minutes
        avg_delivery_time = 35  # minutes
        
        return {
            'total_orders': total_orders,
            'total_revenue': total_revenue,
            'total_customers': unique_customers,
            'average_rating': avg_rating,
            'orders_by_status': status_dict,
            'revenue_growth': revenue_growth,
            'revenue_target': 10000,  # Could be configurable per restaurant
            'new_customers': unique_customers,  # Simplified - would need to track actual new vs returning
            'returning_customers': 0,  # Would need proper tracking
            'customer_growth_percentage': customer_growth,
            'average_preparation_time': avg_prep_time,
            'average_delivery_time': avg_delivery_time,
            'daily_orders': daily_orders,
            'weekly_orders': weekly_orders,
            'monthly_revenue': monthly_revenue,
            'popular_items': popular_items,
        }
    
    def get_daily_orders(self, restaurant, start_date, end_date):
        """
        Get daily order counts for charts
        """
        daily_data = Order.objects.filter(
            restaurant=restaurant,
            created_at__date__gte=start_date,
            created_at__date__lte=end_date
        ).extra(
            select={'day': 'date(created_at)'}
        ).values('day').annotate(
            count=Count('id'),
            revenue=Sum('total_price')
        ).order_by('day')
        
        return [
            {
                'date': item['day'].strftime('%Y-%m-%d'),
                'orders': item['count'],
                'revenue': float(item['revenue'] or 0)
            }
            for item in daily_data
        ]
    
    def get_weekly_orders(self, restaurant, start_date, end_date):
        """
        Get weekly order data for charts
        """
        weekly_data = Order.objects.filter(
            restaurant=restaurant,
            created_at__date__gte=start_date,
            created_at__date__lte=end_date
        ).annotate(
            week=TruncWeek('created_at')
        ).values('week').annotate(
            count=Count('id'),
            revenue=Sum('total_price')
        ).order_by('week')
        
        return [
            {
                'week': item['week'].strftime('%Y-%m-%d'),
                'orders': item['count'],
                'revenue': float(item['revenue'] or 0)
            }
            for item in weekly_data
        ]
    
    def get_monthly_revenue(self, restaurant, start_date, end_date):
        """
        Get monthly revenue data for charts
        """
        monthly_data = Order.objects.filter(
            restaurant=restaurant,
            created_at__date__gte=start_date,
            created_at__date__lte=end_date
        ).annotate(
            month=TruncMonth('created_at')
        ).values('month').annotate(
            revenue=Sum('total_price'),
            count=Count('id')
        ).order_by('month')
        
        return [
            {
                'month': item['month'].strftime('%Y-%m'),
                'revenue': float(item['revenue'] or 0),
                'orders': item['count']
            }
            for item in monthly_data
        ]
    
    def get_popular_items(self, restaurant, start_date, end_date):
        """
        Get popular menu items for the period
        """
        from orders.models import OrderItem
        
        popular_items = OrderItem.objects.filter(
            order__restaurant=restaurant,
            order__created_at__date__gte=start_date,
            order__created_at__date__lte=end_date
        ).values(
            'menu_item__id',
            'menu_item__name',
            'menu_item__price'
        ).annotate(
            order_count=Sum('quantity'),
            total_revenue=Sum(F('quantity') * F('unit_price'))
        ).order_by('-order_count')[:10]
        
        return [
            {
                'id': item['menu_item__id'],
                'name': item['menu_item__name'],
                'price': float(item['menu_item__price']),
                'order_count': item['order_count'],
                'total_revenue': float(item['total_revenue'] or 0)
            }
            for item in popular_items
        ]


class PlatformAnalyticsViewSet(viewsets.ViewSet):
    """
    ViewSet for platform-wide analytics (Admin only)
    """
    permission_classes = [permissions.IsAuthenticated, IsAdminUser]
    serializer_class = PlatformDashboardSerializer
    
    @extend_schema(
        summary="Get platform dashboard analytics",
        description="Get comprehensive platform-wide analytics for admin dashboard"
    )
    @action(detail=False, methods=['get'])
    def dashboard(self, request):
        """
        Get comprehensive platform analytics for admin dashboard
        """
        period = request.query_params.get('period', 'month')
        start_date, end_date = self.get_date_range(period)
        
        # Calculate platform analytics
        analytics_data = self.calculate_platform_analytics(start_date, end_date)
        
        serializer = PlatformDashboardSerializer(analytics_data)
        return Response(serializer.data)
    
    def get_date_range(self, period='month'):
        """
        Get date range based on period
        """
        end_date = timezone.now().date()
        
        if period == 'today':
            start_date = end_date
        elif period == 'week':
            start_date = end_date - timedelta(days=7)
        elif period == 'month':
            start_date = end_date - timedelta(days=30)
        elif period == 'quarter':
            start_date = end_date - timedelta(days=90)
        elif period == 'year':
            start_date = end_date - timedelta(days=365)
        else:
            start_date = end_date - timedelta(days=30)
        
        return start_date, end_date
    
    def calculate_platform_analytics(self, start_date, end_date):
        """
        Calculate platform-wide analytics
        """
        # Total counts
        total_restaurants = Restaurant.objects.count()
        total_drivers = DriverProfile.objects.count()
        total_customers = CustomUser.objects.filter(role='CUSTOMER').count()
        total_orders = Order.objects.count()
        total_revenue = Order.objects.aggregate(Sum('total_price'))['total_price__sum'] or 0
        
        # Monthly growth
        current_month_start = timezone.now().replace(day=1).date()
        new_restaurants_this_month = Restaurant.objects.filter(
            created_at__date__gte=current_month_start
        ).count()
        new_drivers_this_month = DriverProfile.objects.filter(
            created_at__date__gte=current_month_start
        ).count()
        new_customers_this_month = CustomUser.objects.filter(
            role='CUSTOMER',
            date_joined__date__gte=current_month_start
        ).count()
        
        # Performance metrics
        platform_avg_rating = RestaurantReview.objects.aggregate(
            Avg('rating')
        )['rating__avg']
        
        delivered_orders = Order.objects.filter(status='DELIVERED').count()
        successful_delivery_rate = (delivered_orders / total_orders * 100) if total_orders > 0 else 0
        
        # Revenue breakdown (mock data - would need proper commission tracking)
        commission_earned = total_revenue * 0.15  # 15% commission
        delivery_fees_collected = Order.objects.aggregate(
            Sum('delivery_fee')
        )['delivery_fee__sum'] or 0
        
        # Geographic data (simplified)
        top_cities = [
            {'city': 'New York', 'orders': 1250, 'revenue': 45000},
            {'city': 'Los Angeles', 'orders': 980, 'revenue': 35000},
            {'city': 'Chicago', 'orders': 750, 'revenue': 28000},
        ]
        
        # Time series data
        monthly_growth = self.get_monthly_growth()
        revenue_trends = self.get_revenue_trends()
        
        return {
            'total_restaurants': total_restaurants,
            'total_drivers': total_drivers,
            'total_customers': total_customers,
            'total_orders': total_orders,
            'total_revenue': total_revenue,
            'new_restaurants_this_month': new_restaurants_this_month,
            'new_drivers_this_month': new_drivers_this_month,
            'new_customers_this_month': new_customers_this_month,
            'platform_average_rating': platform_avg_rating,
            'average_delivery_time': 35,  # Mock data
            'successful_delivery_rate': successful_delivery_rate,
            'commission_earned': commission_earned,
            'delivery_fees_collected': delivery_fees_collected,
            'top_cities': top_cities,
            'monthly_growth': monthly_growth,
            'revenue_trends': revenue_trends,
        }
    
    def get_monthly_growth(self):
        """
        Get monthly growth data for the past 12 months
        """
        # This is simplified - in a real app, you'd calculate actual monthly growth
        months = []
        for i in range(12):
            month_date = timezone.now().date().replace(day=1) - timedelta(days=30*i)
            months.append({
                'month': month_date.strftime('%Y-%m'),
                'restaurants': 5 + i * 2,
                'drivers': 8 + i * 3,
                'customers': 50 + i * 15,
                'orders': 200 + i * 45
            })
        return list(reversed(months))
    
    def get_revenue_trends(self):
        """
        Get revenue trends for the past 12 months
        """
        revenue_data = Order.objects.filter(
            created_at__gte=timezone.now() - timedelta(days=365)
        ).annotate(
            month=TruncMonth('created_at')
        ).values('month').annotate(
            revenue=Sum('total_price'),
            orders=Count('id')
        ).order_by('month')
        
        return [
            {
                'month': item['month'].strftime('%Y-%m'),
                'revenue': float(item['revenue'] or 0),
                'orders': item['orders']
            }
            for item in revenue_data
        ]


@extend_schema_view(
    list=extend_schema(summary="List dashboard stats", description="List pre-calculated dashboard statistics"),
)
class DashboardStatsViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for pre-calculated dashboard statistics
    """
    serializer_class = DashboardStatsSerializer
    permission_classes = [AnalyticsPermission]
    
    def get_queryset(self):
        # Handle schema generation case
        if getattr(self, 'swagger_fake_view', False):
            return DashboardStats.objects.none()
            
        user = self.request.user
        
        if user.is_staff:
            return DashboardStats.objects.all()
        
        if user.is_restaurant_owner() and hasattr(user, 'restaurant'):
            return DashboardStats.objects.filter(restaurant=user.restaurants.first())
        
        return DashboardStats.objects.none()


@extend_schema_view(
    list=extend_schema(summary="List revenue metrics", description="List detailed revenue tracking data"),
)
class RevenueMetricsViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for revenue metrics and tracking
    """
    serializer_class = RevenueMetricsSerializer
    permission_classes = [AnalyticsPermission]
    
    def get_queryset(self):
        # Handle schema generation case
        if getattr(self, 'swagger_fake_view', False):
            return RevenueMetrics.objects.none()
            
        user = self.request.user
        
        if user.is_staff:
            return RevenueMetrics.objects.all()
        
        if user.is_restaurant_owner() and hasattr(user, 'restaurant'):
            return RevenueMetrics.objects.filter(restaurant=user.restaurants.first())
        
        return RevenueMetrics.objects.none()


@extend_schema_view(
    list=extend_schema(summary="List customer insights", description="List customer behavior analytics"),
)
class CustomerInsightsViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for customer insights and behavior analytics
    """
    serializer_class = CustomerInsightsSerializer
    permission_classes = [AnalyticsPermission]
    
    def get_queryset(self):
        # Handle schema generation case
        if getattr(self, 'swagger_fake_view', False):
            return CustomerInsights.objects.none()
            
        user = self.request.user
        
        if user.is_staff:
            return CustomerInsights.objects.all()
        
        if user.is_restaurant_owner() and hasattr(user, 'restaurant'):
            return CustomerInsights.objects.filter(restaurant=user.restaurants.first())
        
        return CustomerInsights.objects.none()


@extend_schema_view(
    list=extend_schema(summary="List popular menu items", description="List popular menu items analytics"),
)
class PopularMenuItemsViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for popular menu items analytics
    """
    serializer_class = PopularMenuItemsSerializer
    permission_classes = [AnalyticsPermission]
    
    def get_queryset(self):
        # Handle schema generation case
        if getattr(self, 'swagger_fake_view', False):
            return PopularMenuItems.objects.none()
            
        user = self.request.user
        
        if user.is_staff:
            return PopularMenuItems.objects.all()
        
        if user.is_restaurant_owner() and hasattr(user, 'restaurant'):
            return PopularMenuItems.objects.filter(restaurant=user.restaurants.first())
        
        return PopularMenuItems.objects.none()
