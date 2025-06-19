from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    CustomTokenObtainPairView,
    LogoutView,
    UserRegistrationView,
    UserProfileView,
    PasswordChangeView,
    ForgotPasswordView,
    CustomerListView,
    DriverListView,
    RestaurantOwnerListView,
)

app_name = 'users'

urlpatterns = [
    # Authentication
    path('token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('logout/', LogoutView.as_view(), name='logout'),
    
    # User management
    path('register/', UserRegistrationView.as_view(), name='register'),
    path('profile/', UserProfileView.as_view(), name='profile'),
    path('change-password/', PasswordChangeView.as_view(), name='change_password'),
    path('forgot-password/', ForgotPasswordView.as_view(), name='forgot_password'),
    
    # Admin views
    path('customers/', CustomerListView.as_view(), name='customer_list'),
    path('drivers/', DriverListView.as_view(), name='driver_list'),
    path('restaurant-owners/', RestaurantOwnerListView.as_view(), name='restaurant_owner_list'),
]