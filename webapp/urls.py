# webapp/urls.py
from django.urls import path
from . import views

app_name = 'webapp'

urlpatterns = [
    # Existing URLs
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('profile/', views.profile_view, name='profile'),
    
    # Dashboard URLs
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('dashboard/restaurant/', views.restaurant_dashboard, name='restaurant_dashboard'),
    path('dashboard/restaurant/new/', views.restaurant_dashboard_new, name='restaurant_dashboard_new'),
    path('dashboard/customer/', views.customer_dashboard, name='customer_dashboard'),
    path('dashboard/driver/', views.driver_dashboard, name='driver_dashboard'),
    
    # Restaurant URLs
    path('restaurants/', views.restaurant_list, name='restaurant_list'),
    path('restaurants/<uuid:restaurant_id>/', views.restaurant_detail, name='restaurant_detail'),
    
    # Customer URLs
    path('my-orders/', views.customer_order_list, name='customer_order_list'),
    
    # Restaurant Owner URLs
    path('my-restaurant/', views.manage_restaurant, name='manage_restaurant'),
    path('my-restaurant/orders/', views.restaurant_orders, name='restaurant_orders'),
    path('my-restaurant/menu/', views.menu_management, name='menu_management'),
    path('my-restaurant/menu/categories/add/', views.menu_category_create, name='menu_category_create'),
    path('my-restaurant/menu/categories/<uuid:category_id>/edit/', views.menu_category_edit, name='menu_category_edit'),
    path('my-restaurant/menu/categories/<uuid:category_id>/add-item/', views.menu_item_create, name='menu_item_create_with_category'),
    path('my-restaurant/menu/items/add/', views.menu_item_create, name='menu_item_create'),
    path('my-restaurant/menu/items/<uuid:item_id>/edit/', views.menu_item_edit, name='menu_item_edit'),
    
    # Driver URLs
    path('driver/tasks/', views.driver_task_list, name='driver_task_list'),
    path('driver/earnings/', views.driver_earnings_report, name='driver_earnings_report'),
]