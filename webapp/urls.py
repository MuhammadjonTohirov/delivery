from django.urls import path
from .views import (
    HomePageView, 
    LoginPageView, 
    RegisterPageView,
    CustomerDashboardView,
    RestaurantDashboardView,
    DriverDashboardView,
    ProfilePageView,
    RestaurantListView,
    RestaurantDetailView,
    ManageRestaurantView,
    MenuManagementView,
    MenuCategoryCreateView,
    MenuCategoryEditView,
    MenuItemCreateView,
    MenuItemEditView,
    RestaurantOrderListView,
    DriverTaskListView,
    DriverEarningsView
)

app_name = 'webapp'

urlpatterns = [
    path('', HomePageView.as_view(), name='home'),
    path('login/', LoginPageView.as_view(), name='login'),
    path('register/', RegisterPageView.as_view(), name='register'),
    # It's better to have a generic profile view that then loads user-specific data
    # For now, these are direct links to placeholder dashboard templates
    path('dashboard/customer/', CustomerDashboardView.as_view(), name='customer_dashboard'),
    path('dashboard/restaurant/', RestaurantDashboardView.as_view(), name='restaurant_dashboard'),
    path('dashboard/driver/', DriverDashboardView.as_view(), name='driver_dashboard'),
    path('profile/', ProfilePageView.as_view(), name='profile'),
    path('restaurants/', RestaurantListView.as_view(), name='restaurant_list'),
    path('restaurants/<uuid:restaurant_id>/', RestaurantDetailView.as_view(), name='restaurant_detail'),
    path('my-restaurant/manage/', ManageRestaurantView.as_view(), name='manage_restaurant'),
    path('my-restaurant/menu/', MenuManagementView.as_view(), name='menu_management'),
    path('my-restaurant/menu/categories/add/', MenuCategoryCreateView.as_view(), name='menu_category_create'),
    path('my-restaurant/menu/categories/<uuid:category_id>/edit/', MenuCategoryEditView.as_view(), name='menu_category_edit'),
    path('my-restaurant/menu/items/add/', MenuItemCreateView.as_view(), name='menu_item_create'), # Generic add item
    path('my-restaurant/menu/categories/<uuid:category_id>/add-item/', MenuItemCreateView.as_view(), name='menu_item_create_in_category'), # Add item to specific category
    path('my-restaurant/menu/items/<uuid:item_id>/edit/', MenuItemEditView.as_view(), name='menu_item_edit'),
    path('my-restaurant/orders/', RestaurantOrderListView.as_view(), name='restaurant_orders'),
    path('driver/tasks/', DriverTaskListView.as_view(), name='driver_task_list'),
    path('driver/earnings/', DriverEarningsView.as_view(), name='driver_earnings_report'),
]