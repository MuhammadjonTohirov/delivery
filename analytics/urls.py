from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AdminAnalyticsViewSet, RestaurantAnalyticsViewSet, DriverAnalyticsViewSet, ReportsViewSet

router = DefaultRouter()
router.register(r'admin', AdminAnalyticsViewSet, basename='admin-analytics')
router.register(r'restaurant', RestaurantAnalyticsViewSet, basename='restaurant-analytics')
router.register(r'driver', DriverAnalyticsViewSet, basename='driver-analytics')
router.register(r'reports', ReportsViewSet, basename='reports')

app_name = 'analytics'

urlpatterns = [
    path('', include(router.urls)),
]
