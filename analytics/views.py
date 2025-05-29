from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Count, Sum, Avg, Q, F
from django.utils import timezone
from datetime import timedelta, datetime
from decimal import Decimal

from orders.models import Order, OrderItem
from restaurants.models import Restaurant, MenuItem
from users.models import CustomUser
from drivers.models import DriverEarning, DriverTask
from payments.models import Payment
from users.permissions import IsAdminUser, IsRestaurantOwner, IsDriver
from drf_spectacular.utils import extend_schema, extend_schema_view


@extend_schema_view(
    retrieve=extend_schema(summary="Get admin analytics dashboard", description="Get comprehensive analytics for admins"),
)
class AdminAnalyticsViewSet(viewsets.ViewSet):
    """Analytics dashboard for admins"""
    permission_classes = [permissions.IsAuthenticated, IsAdminUser]
    
    @extend_schema(
        summary="Get dashboard overview",
        description="Get key metrics overview for admin dashboard"
    )
    @action(detail=False, methods=['get'])
    def dashboard(self, request):
        # Date range parameters
        days = int(request.query_params.get('days', 30))
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        
        # Key metrics
        total_orders = Order.objects.filter(created_at__gte=start_date).count()
        total_revenue = Order.objects.filter(
            created_at__gte=start_date,
            status='DELIVERED'
        ).aggregate(Sum('total_price'))['total_price__sum'] or 0
        
        active_restaurants = Restaurant.objects.filter(is_open=True).count()
        active_drivers = CustomUser.objects.filter(role='DRIVER', is_active=True).count()
        total_customers = CustomUser.objects.filter(role='CUSTOMER', is_active=True).count()
        
        # Order status breakdown
        order_statuses = Order.objects.filter(created_at__gte=start_date).values('status').annotate(
            count=Count('id')
        ).order_by('status')
        
        # Revenue by day
        daily_revenue = []
        for i in range(days):
            day = start_date + timedelta(days=i)
            day_revenue = Order.objects.filter(
                created_at__date=day.date(),
                status='DELIVERED'
            ).aggregate(Sum('total_price'))['total_price__sum'] or 0
            
            daily_revenue.append({
                'date': day.date().isoformat(),
                'revenue': float(day_revenue)
            })
        
        # Top restaurants by orders
        top_restaurants = Restaurant.objects.annotate(
            order_count=Count('orders', filter=Q(orders__created_at__gte=start_date))
        ).order_by('-order_count')[:10]
        
        # Top menu items
        top_items = MenuItem.objects.annotate(
            order_count=Count('orderitem', filter=Q(orderitem__order__created_at__gte=start_date))
        ).order_by('-order_count')[:10]
        
        return Response({
            'overview': {
                'total_orders': total_orders,
                'total_revenue': float(total_revenue),
                'active_restaurants': active_restaurants,
                'active_drivers': active_drivers,
                'total_customers': total_customers,
                'avg_order_value': float(total_revenue / total_orders) if total_orders > 0 else 0
            },
            'order_statuses': list(order_statuses),
            'daily_revenue': daily_revenue,
            'top_restaurants': [
                {
                    'id': str(r.id),
                    'name': r.name,
                    'order_count': r.order_count
                } for r in top_restaurants
            ],
            'top_menu_items': [
                {
                    'id': str(item.id),
                    'name': item.name,
                    'restaurant': item.restaurant.name,
                    'order_count': item.order_count
                } for item in top_items
            ]
        })
    
    @extend_schema(
        summary="Get user analytics",
        description="Get user registration and activity analytics"
    )
    @action(detail=False, methods=['get'])
    def users(self, request):
        days = int(request.query_params.get('days', 30))
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        
        # User registrations by role
        user_registrations = CustomUser.objects.filter(
            date_joined__gte=start_date
        ).values('role').annotate(count=Count('id'))
        
        # Daily registrations
        daily_registrations = []
        for i in range(days):
            day = start_date + timedelta(days=i)
            day_count = CustomUser.objects.filter(
                date_joined__date=day.date()
            ).count()
            
            daily_registrations.append({
                'date': day.date().isoformat(),
                'registrations': day_count
            })
        
        # Active users (placed an order in the period)
        active_customers = CustomUser.objects.filter(
            role='CUSTOMER',
            orders__created_at__gte=start_date
        ).distinct().count()
        
        return Response({
            'user_registrations': list(user_registrations),
            'daily_registrations': daily_registrations,
            'active_customers': active_customers
        })
    
    @extend_schema(
        summary="Get payment analytics",
        description="Get payment and revenue analytics"
    )
    @action(detail=False, methods=['get'])
    def payments(self, request):
        days = int(request.query_params.get('days', 30))
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        
        # Payment method breakdown
        payment_methods = Payment.objects.filter(
            created_at__gte=start_date,
            status='COMPLETED'
        ).values('payment_method__type').annotate(
            count=Count('id'),
            total_amount=Sum('amount')
        )
        
        # Failed payments
        failed_payments = Payment.objects.filter(
            created_at__gte=start_date,
            status='FAILED'
        ).count()
        
        total_payments = Payment.objects.filter(created_at__gte=start_date).count()
        
        return Response({
            'payment_methods': list(payment_methods),
            'failed_payments': failed_payments,
            'success_rate': ((total_payments - failed_payments) / total_payments * 100) if total_payments > 0 else 0
        })


@extend_schema_view(
    retrieve=extend_schema(summary="Get restaurant analytics", description="Get analytics for restaurant owners"),
)
class RestaurantAnalyticsViewSet(viewsets.ViewSet):
    """Analytics dashboard for restaurant owners"""
    permission_classes = [permissions.IsAuthenticated, IsRestaurantOwner]
    
    @extend_schema(
        summary="Get restaurant dashboard",
        description="Get analytics for the restaurant owner's restaurant"
    )
    @action(detail=False, methods=['get'])
    def dashboard(self, request):
        try:
            restaurant = request.user.restaurant
        except:
            return Response({"error": "No restaurant associated with this user."}, status=404)
        
        days = int(request.query_params.get('days', 30))
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        
        # Restaurant specific metrics
        total_orders = restaurant.orders.filter(created_at__gte=start_date).count()
        total_revenue = restaurant.orders.filter(
            created_at__gte=start_date,
            status='DELIVERED'
        ).aggregate(Sum('total_price'))['total_price__sum'] or 0
        
        # Order status breakdown
        order_statuses = restaurant.orders.filter(created_at__gte=start_date).values('status').annotate(
            count=Count('id')
        )
        
        # Popular menu items
        popular_items = MenuItem.objects.filter(
            restaurant=restaurant
        ).annotate(
            order_count=Count('orderitem', filter=Q(orderitem__order__created_at__gte=start_date))
        ).order_by('-order_count')[:10]
        
        # Daily revenue
        daily_revenue = []
        for i in range(days):
            day = start_date + timedelta(days=i)
            day_revenue = restaurant.orders.filter(
                created_at__date=day.date(),
                status='DELIVERED'
            ).aggregate(Sum('total_price'))['total_price__sum'] or 0
            
            daily_revenue.append({
                'date': day.date().isoformat(),
                'revenue': float(day_revenue)
            })
        
        # Average order value
        avg_order_value = restaurant.orders.filter(
            created_at__gte=start_date,
            status='DELIVERED'
        ).aggregate(Avg('total_price'))['total_price__avg'] or 0
        
        # Peak hours analysis
        peak_hours = restaurant.orders.filter(
            created_at__gte=start_date
        ).extra(
            select={'hour': 'EXTRACT(hour FROM created_at)'}
        ).values('hour').annotate(
            count=Count('id')
        ).order_by('-count')
        
        return Response({
            'overview': {
                'total_orders': total_orders,
                'total_revenue': float(total_revenue),
                'avg_order_value': float(avg_order_value),
                'menu_items_count': restaurant.menu_items.count()
            },
            'order_statuses': list(order_statuses),
            'daily_revenue': daily_revenue,
            'popular_items': [
                {
                    'id': str(item.id),
                    'name': item.name,
                    'order_count': item.order_count,
                    'price': float(item.price)
                } for item in popular_items
            ],
            'peak_hours': list(peak_hours)
        })


@extend_schema_view(
    retrieve=extend_schema(summary="Get driver analytics", description="Get analytics for drivers"),
)
class DriverAnalyticsViewSet(viewsets.ViewSet):
    """Analytics dashboard for drivers"""
    permission_classes = [permissions.IsAuthenticated, IsDriver]
    
    @extend_schema(
        summary="Get driver dashboard",
        description="Get analytics for the driver"
    )
    @action(detail=False, methods=['get'])
    def dashboard(self, request):
        try:
            driver_profile = request.user.driver_profile
        except:
            return Response({"error": "No driver profile associated with this user."}, status=404)
        
        days = int(request.query_params.get('days', 30))
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        
        # Driver specific metrics
        total_deliveries = DriverTask.objects.filter(
            driver=driver_profile,
            status='DELIVERED',
            completed_at__gte=start_date
        ).count()
        
        total_earnings = DriverEarning.objects.filter(
            driver=driver_profile,
            timestamp__gte=start_date
        ).aggregate(Sum('amount'))['amount__sum'] or 0
        
        # Task status breakdown
        task_statuses = DriverTask.objects.filter(
            driver=driver_profile,
            assigned_at__gte=start_date
        ).values('status').annotate(count=Count('id'))
        
        # Daily earnings
        daily_earnings = []
        for i in range(days):
            day = start_date + timedelta(days=i)
            day_earnings = DriverEarning.objects.filter(
                driver=driver_profile,
                timestamp__date=day.date()
            ).aggregate(Sum('amount'))['amount__sum'] or 0
            
            daily_earnings.append({
                'date': day.date().isoformat(),
                'earnings': float(day_earnings)
            })
        
        # Average earnings per delivery
        avg_per_delivery = float(total_earnings / total_deliveries) if total_deliveries > 0 else 0
        
        # Acceptance rate
        total_assigned = DriverTask.objects.filter(
            driver=driver_profile,
            assigned_at__gte=start_date
        ).count()
        
        accepted_tasks = DriverTask.objects.filter(
            driver=driver_profile,
            assigned_at__gte=start_date,
            status__in=['ACCEPTED', 'PICKED_UP', 'DELIVERED']
        ).count()
        
        acceptance_rate = (accepted_tasks / total_assigned * 100) if total_assigned > 0 else 0
        
        return Response({
            'overview': {
                'total_deliveries': total_deliveries,
                'total_earnings': float(total_earnings),
                'avg_per_delivery': avg_per_delivery,
                'acceptance_rate': round(acceptance_rate, 2)
            },
            'task_statuses': list(task_statuses),
            'daily_earnings': daily_earnings
        })


class ReportsViewSet(viewsets.ViewSet):
    """Generate detailed reports for admin users"""
    permission_classes = [permissions.IsAuthenticated, IsAdminUser]
    
    @extend_schema(
        summary="Generate sales report",
        description="Generate detailed sales report with filters"
    )
    @action(detail=False, methods=['get'])
    def sales_report(self, request):
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        restaurant_id = request.query_params.get('restaurant_id')
        
        # Default to last 30 days if no dates provided
        if not start_date or not end_date:
            end_date = timezone.now()
            start_date = end_date - timedelta(days=30)
        else:
            start_date = datetime.fromisoformat(start_date)
            end_date = datetime.fromisoformat(end_date)
        
        # Base queryset
        orders_qs = Order.objects.filter(
            created_at__gte=start_date,
            created_at__lte=end_date,
            status='DELIVERED'
        )
        
        # Filter by restaurant if specified
        if restaurant_id:
            orders_qs = orders_qs.filter(restaurant_id=restaurant_id)
        
        # Generate report data
        total_orders = orders_qs.count()
        total_revenue = orders_qs.aggregate(Sum('total_price'))['total_price__sum'] or 0
        avg_order_value = orders_qs.aggregate(Avg('total_price'))['total_price__avg'] or 0
        
        # Sales by restaurant
        restaurant_sales = orders_qs.values(
            'restaurant__name'
        ).annotate(
            order_count=Count('id'),
            revenue=Sum('total_price')
        ).order_by('-revenue')
        
        # Sales by day
        daily_sales = orders_qs.extra(
            select={'day': 'DATE(created_at)'}
        ).values('day').annotate(
            order_count=Count('id'),
            revenue=Sum('total_price')
        ).order_by('day')
        
        return Response({
            'period': {
                'start_date': start_date.date().isoformat(),
                'end_date': end_date.date().isoformat()
            },
            'summary': {
                'total_orders': total_orders,
                'total_revenue': float(total_revenue),
                'avg_order_value': float(avg_order_value)
            },
            'restaurant_sales': list(restaurant_sales),
            'daily_sales': list(daily_sales)
        })
    
    @extend_schema(
        summary="Generate customer report",
        description="Generate customer behavior and analytics report"
    )
    @action(detail=False, methods=['get'])
    def customer_report(self, request):
        days = int(request.query_params.get('days', 30))
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        
        # Customer metrics
        total_customers = CustomUser.objects.filter(role='CUSTOMER').count()
        active_customers = CustomUser.objects.filter(
            role='CUSTOMER',
            orders__created_at__gte=start_date
        ).distinct().count()
        
        new_customers = CustomUser.objects.filter(
            role='CUSTOMER',
            date_joined__gte=start_date
        ).count()
        
        # Customer order patterns
        repeat_customers = CustomUser.objects.filter(
            role='CUSTOMER'
        ).annotate(
            order_count=Count('orders', filter=Q(orders__created_at__gte=start_date))
        ).filter(order_count__gt=1).count()
        
        # Average orders per customer
        avg_orders_per_customer = Order.objects.filter(
            created_at__gte=start_date
        ).values('customer').annotate(
            order_count=Count('id')
        ).aggregate(Avg('order_count'))['order_count__avg'] or 0
        
        # Customer lifetime value (simplified)
        customer_ltv = CustomUser.objects.filter(
            role='CUSTOMER'
        ).annotate(
            total_spent=Sum('orders__total_price', filter=Q(orders__status='DELIVERED'))
        ).aggregate(Avg('total_spent'))['total_spent__avg'] or 0
        
        return Response({
            'customer_metrics': {
                'total_customers': total_customers,
                'active_customers': active_customers,
                'new_customers': new_customers,
                'repeat_customers': repeat_customers,
                'repeat_rate': (repeat_customers / active_customers * 100) if active_customers > 0 else 0
            },
            'behavior_metrics': {
                'avg_orders_per_customer': float(avg_orders_per_customer),
                'customer_lifetime_value': float(customer_ltv)
            }
        })
