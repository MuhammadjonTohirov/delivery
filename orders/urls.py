from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import OrderViewSet
from .dashboard_views import dashboard_statistics, dashboard_recent_orders, dashboard_restaurants

router = DefaultRouter()
router.register(r'', OrderViewSet, basename='order')

app_name = 'orders'

urlpatterns = [
    path('dashboard/statistics/', dashboard_statistics, name='dashboard-statistics'),
    path('dashboard/recent-orders/', dashboard_recent_orders, name='dashboard-recent-orders'),
    path('dashboard/restaurants/', dashboard_restaurants, name='dashboard-restaurants'),
    path('', include(router.urls)),
]