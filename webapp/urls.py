from django.urls import path
from . import views

app_name = 'webapp'

urlpatterns = [
    # Public pages
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
    path('profile/', views.profile_view, name='profile'),
    
    # Restaurant public pages
    path('restaurants/', views.restaurant_list_view, name='restaurant_list'),
    path('restaurants/<uuid:restaurant_id>/', views.restaurant_detail_view, name='restaurant_detail'),
    
    # Dashboard pages
    path('dashboard/restaurant/', views.RestaurantDashboardView.as_view(), name='restaurant_dashboard'),
    path('dashboard/customer/', views.CustomerDashboardView.as_view(), name='customer_dashboard'),
    path('dashboard/driver/', views.DriverDashboardView.as_view(), name='driver_dashboard'),
    path('dashboard/admin/', views.admin_dashboard_view, name='admin_dashboard'),
    
    # Restaurant management
    path('restaurant/orders/', views.restaurant_orders_view, name='restaurant_orders'),
    path('restaurant/menu/', views.restaurant_menu_view, name='restaurant_menu'),
    
    # Customer pages
    path('customer/orders/', views.customer_orders_view, name='customer_orders'),
    
    # Driver pages
    path('driver/tasks/', views.driver_tasks_view, name='driver_tasks'),
    path('driver/earnings/', views.driver_earnings_view, name='driver_earnings'),
    
    # AJAX endpoints
    path('ajax/update-order-status/', views.ajax_update_order_status, name='ajax_update_order_status'),
    path('ajax/driver-location/', views.ajax_driver_update_location, name='ajax_driver_location'),
]
