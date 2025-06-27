from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView
)

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # API documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    
    # Authentication & User Management
    path('api/auth/', include('users.urls')),
    
    # Search functionality
    path('api/', include('core.urls')),
    
    # Core Business Operations
    path('api/restaurants/', include('restaurants.urls')),
    path('api/orders/', include('orders.urls')),
    path('api/customers/', include('orders.customers_urls')),
    path('api/cart/', include('cart.urls')),
    
    # Delivery & Logistics
    path('api/drivers/', include('drivers.urls')),
    path('api/geography/', include('geography.urls')),
    
    # Financial Operations
    path('api/payments/', include('payments.urls')),
    path('api/promotions/', include('promotions.urls')),
    
    # Communication & Analytics
    path('api/notifications/', include('notifications.urls')),
    path('api/analytics/', include('analytics.urls')),
    
    # System Settings
    path('api/settings/', include('settings.urls')),
    
    # Frontend URLs
    path('', include('webapp.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)