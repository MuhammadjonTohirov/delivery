from django.urls import path
from . import views

app_name = 'webapp'

urlpatterns = [
    # Main index page
    path('', views.index, name='index'),
    
    # Auth pages
    path('register/', views.register, name='register'),
    
    # Keep minimal AJAX endpoints for backwards compatibility
    path('ajax/update-order-status/', views.ajax_update_order_status, name='ajax_update_order_status'),
    path('ajax/driver-location/', views.ajax_driver_update_location, name='ajax_driver_location'),
]
