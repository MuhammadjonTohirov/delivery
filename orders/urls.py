from django.urls import path, include
from rest_framework.routers import DefaultRouter

from orders.extra.order_details import order_details_enhanced
from .views import OrderViewSet
from .extra.dashboard_views import dashboard_statistics, dashboard_recent_orders, dashboard_restaurants
from .customer_views import customers_list, customer_summary

router = DefaultRouter()
router.register(r'', OrderViewSet, basename='order')

app_name = 'orders'

urlpatterns = [
    path('dashboard/statistics/', dashboard_statistics, name='dashboard-statistics'),
    path('dashboard/recent-orders/', dashboard_recent_orders, name='dashboard-recent-orders'),
    path('dashboard/restaurants/', dashboard_restaurants, name='dashboard-restaurants'),
    path('<str:order_id>/details/', order_details_enhanced, name='order_details_enhanced'),

    path('', include(router.urls)),
]