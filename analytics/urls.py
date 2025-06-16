from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    AnalyticsEventViewSet,
    RestaurantAnalyticsViewSet,
    PlatformAnalyticsViewSet,
    DashboardStatsViewSet,
    RevenueMetricsViewSet,
    CustomerInsightsViewSet,
    PopularMenuItemsViewSet
)
from .analytics_views import business_performance, menu_performance, customer_analytics

router = DefaultRouter()
router.register(r'events', AnalyticsEventViewSet, basename='analytics-event')
router.register(r'restaurant', RestaurantAnalyticsViewSet, basename='restaurant-analytics')
router.register(r'platform', PlatformAnalyticsViewSet, basename='platform-analytics')
router.register(r'dashboard-stats', DashboardStatsViewSet, basename='dashboard-stats')
router.register(r'revenue', RevenueMetricsViewSet, basename='revenue-metrics')
router.register(r'customer-insights', CustomerInsightsViewSet, basename='customer-insights')
router.register(r'popular-items', PopularMenuItemsViewSet, basename='popular-items')

app_name = 'analytics'

urlpatterns = [
    # New analytics endpoints
    path('business-performance/', business_performance, name='business-performance'),
    path('menu-performance/', menu_performance, name='menu-performance'),
    path('customer-analytics/', customer_analytics, name='customer-analytics'),
    
    # Existing endpoints
    path('', include(router.urls)),
]
