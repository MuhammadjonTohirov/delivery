from rest_framework import serializers
from .models import AnalyticsEvent, DashboardStats, RevenueMetrics, CustomerInsights, PopularMenuItems
from datetime import datetime, timedelta


class AnalyticsEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnalyticsEvent
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class DashboardStatsSerializer(serializers.ModelSerializer):
    restaurant_name = serializers.CharField(source='restaurant.name', read_only=True)
    
    class Meta:
        model = DashboardStats
        fields = [
            'id', 'restaurant', 'restaurant_name', 'date',
            'total_orders', 'completed_orders', 'cancelled_orders', 'pending_orders',
            'total_revenue', 'average_order_value',
            'new_customers', 'returning_customers',
            'average_preparation_time', 'average_delivery_time',
            'created_at', 'updated_at'
        ]


class RevenueMetricsSerializer(serializers.ModelSerializer):
    restaurant_name = serializers.CharField(source='restaurant.name', read_only=True)
    
    class Meta:
        model = RevenueMetrics
        fields = [
            'id', 'restaurant', 'restaurant_name', 'date', 'hour',
            'gross_revenue', 'net_revenue', 'delivery_fees', 'taxes', 'commission',
            'dine_in_orders', 'takeout_orders', 'delivery_orders',
            'created_at', 'updated_at'
        ]


class CustomerInsightsSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source='customer.full_name', read_only=True)
    customer_email = serializers.CharField(source='customer.email', read_only=True)
    restaurant_name = serializers.CharField(source='restaurant.name', read_only=True)
    
    class Meta:
        model = CustomerInsights
        fields = [
            'id', 'customer', 'customer_name', 'customer_email',
            'restaurant', 'restaurant_name',
            'total_orders', 'total_spent', 'average_order_value',
            'favorite_cuisine', 'preferred_order_time', 'last_order_date',
            'app_opens', 'menu_views', 'search_count',
            'created_at', 'updated_at'
        ]


class PopularMenuItemsSerializer(serializers.ModelSerializer):
    menu_item_name = serializers.CharField(source='menu_item.name', read_only=True)
    menu_item_price = serializers.DecimalField(source='menu_item.price', max_digits=10, decimal_places=2, read_only=True)
    restaurant_name = serializers.CharField(source='restaurant.name', read_only=True)
    
    class Meta:
        model = PopularMenuItems
        fields = [
            'id', 'menu_item', 'menu_item_name', 'menu_item_price',
            'restaurant', 'restaurant_name', 'date',
            'order_count', 'view_count', 'total_revenue',
            'popularity_rank', 'revenue_rank',
            'created_at', 'updated_at'
        ]


class RestaurantDashboardSerializer(serializers.Serializer):
    """
    Comprehensive serializer for restaurant dashboard data
    """
    # Basic stats
    total_orders = serializers.IntegerField()
    total_revenue = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_customers = serializers.IntegerField()
    average_rating = serializers.DecimalField(max_digits=3, decimal_places=2, allow_null=True)
    
    # Order breakdown
    orders_by_status = serializers.DictField()
    
    # Revenue metrics
    revenue_growth = serializers.DecimalField(max_digits=5, decimal_places=2, allow_null=True)
    revenue_target = serializers.DecimalField(max_digits=12, decimal_places=2, allow_null=True)
    
    # Customer metrics
    new_customers = serializers.IntegerField()
    returning_customers = serializers.IntegerField()
    customer_growth_percentage = serializers.DecimalField(max_digits=5, decimal_places=2, allow_null=True)
    
    # Performance metrics
    average_preparation_time = serializers.IntegerField()
    average_delivery_time = serializers.IntegerField()
    
    # Time series data
    daily_orders = serializers.ListField(child=serializers.DictField(), required=False)
    weekly_orders = serializers.ListField(child=serializers.DictField(), required=False)
    monthly_revenue = serializers.ListField(child=serializers.DictField(), required=False)
    
    # Popular items
    popular_items = PopularMenuItemsSerializer(many=True, required=False)
    
    # Recent activity
    recent_events = AnalyticsEventSerializer(many=True, required=False)


class PlatformDashboardSerializer(serializers.Serializer):
    """
    Platform-wide dashboard statistics for admin users
    """
    # Platform totals
    total_restaurants = serializers.IntegerField()
    total_drivers = serializers.IntegerField()
    total_customers = serializers.IntegerField()
    total_orders = serializers.IntegerField()
    total_revenue = serializers.DecimalField(max_digits=12, decimal_places=2)
    
    # Growth metrics
    new_restaurants_this_month = serializers.IntegerField()
    new_drivers_this_month = serializers.IntegerField()
    new_customers_this_month = serializers.IntegerField()
    
    # Performance metrics
    platform_average_rating = serializers.DecimalField(max_digits=3, decimal_places=2, allow_null=True)
    average_delivery_time = serializers.IntegerField()
    successful_delivery_rate = serializers.DecimalField(max_digits=5, decimal_places=2)
    
    # Revenue breakdown
    commission_earned = serializers.DecimalField(max_digits=12, decimal_places=2)
    delivery_fees_collected = serializers.DecimalField(max_digits=12, decimal_places=2)
    
    # Geographic data
    top_cities = serializers.ListField(child=serializers.DictField())
    
    # Time series
    monthly_growth = serializers.ListField(child=serializers.DictField())
    revenue_trends = serializers.ListField(child=serializers.DictField())


class DateRangeSerializer(serializers.Serializer):
    """
    Serializer for date range filtering
    """
    start_date = serializers.DateField(required=False)
    end_date = serializers.DateField(required=False)
    period = serializers.ChoiceField(
        choices=['today', 'week', 'month', 'quarter', 'year'],
        required=False,
        default='month'
    )
    
    def validate(self, data):
        if data.get('start_date') and data.get('end_date'):
            if data['start_date'] > data['end_date']:
                raise serializers.ValidationError("Start date must be before end date")
        return data
