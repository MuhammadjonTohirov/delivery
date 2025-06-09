# Django Backend - Enhanced Order Details API
# File: views/order_details.py

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.db.models import Prefetch
from decimal import Decimal
import json

from orders.models import Order

# Assuming your existing models (update imports based on your actual structure)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def order_details_enhanced(request, order_id):
    """
    Enhanced order details endpoint that provides comprehensive information
    including user info, menu items with images, and restaurant details
    """
    try:
        # Get order with optimized prefetching
        order = get_object_or_404(
            Order.objects.prefetch_related(
                'items__menu_item__images',
                'items__menu_item__category',
                'customer__customerprofile',
                'restaurant__restaurantprofile',
                'driver__driverprofile',
                'driver__driverlocation_set'
            ).select_related(
                'customer',
                'restaurant', 
                'driver'
            ),
            id=order_id
        )
        
        # Check permission - user can only view their own orders (or admin/restaurant)
        if not can_view_order(request.user, order):
            return Response(
                {'error': 'Access denied'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get image size preference
        image_size = request.GET.get('image_size', 'medium')
        include_driver_location = request.GET.get('include_driver_location', 'true').lower() == 'true'
        
        # Build comprehensive response
        response_data = {
            # Basic Order Information
            'id': order.id,
            'order_number': getattr(order, 'order_number', f"ORD-{order.id}"),
            'status': order.status,
            'status_display': order.get_status_display(),
            'created_at': order.created_at.isoformat(),
            'updated_at': order.updated_at.isoformat(),
            'estimated_delivery_time': order.estimated_delivery_time.isoformat() if hasattr(order, 'estimated_delivery_time') and order.estimated_delivery_time else None,
            
            # Customer Information
            'customer': serialize_customer(order.customer),
            
            # Restaurant Information  
            'restaurant': serialize_restaurant_detailed(order.restaurant),
            
            # Delivery Information
            'delivery_address': order.delivery_address,
            'delivery_lat': str(order.delivery_lat) if order.delivery_lat else None,
            'delivery_lng': str(order.delivery_lng) if order.delivery_lng else None,
            'delivery_instructions': getattr(order, 'delivery_instructions', ''),
            
            # Order Items with Full Menu Details
            'items': serialize_order_items_detailed(order.items.all(), image_size),
            
            # Pricing Breakdown
            'subtotal': calculate_subtotal(order.items.all()),
            'delivery_fee': str(order.delivery_fee) if hasattr(order, 'delivery_fee') and order.delivery_fee else '0.00',
            'tax': calculate_tax(order),
            'discount': str(order.discount) if hasattr(order, 'discount') and order.discount else None,
            'total_price': str(order.total_price),
            
            # Additional Information
            'notes': getattr(order, 'notes', ''),
            'payment_method': getattr(order, 'payment_method', ''),
            'payment_status': getattr(order, 'payment_status', ''),
            
            # Driver Information (if assigned)
            'driver': serialize_driver_info(order.driver, include_driver_location) if order.driver else None
        }
        
        return Response(response_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {'error': f'Failed to fetch order details: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

def can_view_order(user, order):
    """Check if user has permission to view this order"""
    if user.is_staff or user.is_superuser:
        return True
    if hasattr(user, 'usertype') and user.usertype.is_admin:
        return True
    if order.customer == user:
        return True
    if hasattr(user, 'usertype') and user.usertype.is_restaurant_owner:
        if order.restaurant.owner == user:
            return True
    if hasattr(user, 'usertype') and user.usertype.is_driver:
        if order.driver == user:
            return True
    return False

def serialize_customer(customer):
    """Serialize customer with profile information"""
    return {
        'id': customer.id,
        'full_name': customer.full_name,
        'email': customer.email,
        'phone': getattr(customer, 'phone', ''),
        'avatar': customer.avatar.url if customer.avatar else None,
        'user_type': 'CUSTOMER'
    }

def serialize_restaurant_detailed(restaurant):
    """Serialize restaurant with detailed information"""
    restaurant_profile = getattr(restaurant, 'restaurantprofile', None)
    
    return {
        'id': restaurant.id,
        'name': restaurant.name,
        'description': restaurant_profile.description if restaurant_profile else '',
        'logo': restaurant_profile.logo.url if restaurant_profile and restaurant_profile.logo else None,
        'address': restaurant_profile.address if restaurant_profile else '',
        'phone': restaurant_profile.phone if restaurant_profile else '',
        'rating': float(restaurant_profile.rating) if restaurant_profile and restaurant_profile.rating else None,
        'delivery_fee': str(restaurant_profile.delivery_fee) if restaurant_profile and restaurant_profile.delivery_fee else '0.00'
    }

def serialize_order_items_detailed(order_items, image_size='medium'):
    """Serialize order items with complete menu item details"""
    items = []
    
    for order_item in order_items:
        menu_item = order_item.menu_item
        
        # Get menu item images
        menu_item_images = serialize_menu_item_images(menu_item.images.all(), image_size)
        
        # Get dietary information
        dietary_info = []
        if hasattr(menu_item, 'dietary_tags'):
            dietary_info = [tag.name for tag in menu_item.dietary_tags.all()]
        elif hasattr(menu_item, 'dietary_info'):
            dietary_info = menu_item.dietary_info.split(',') if menu_item.dietary_info else []
        
        # Build menu item details
        menu_item_details = {
            'id': menu_item.id,
            'name': menu_item.name,
            'description': menu_item.description,
            'price': str(menu_item.price),
            'category': menu_item.category.name if menu_item.category else '',
            'images': menu_item_images,
            'dietary_info': dietary_info,
            'preparation_time': getattr(menu_item, 'preparation_time', None),
            'availability': getattr(menu_item, 'is_available', True),
            'restaurant_id': menu_item.restaurant.id
        }
        
        # Get customizations
        customizations = []
        if hasattr(order_item, 'customizations'):
            customizations = order_item.customizations.split(',') if order_item.customizations else []
        
        item_data = {
            'id': order_item.id,
            'menu_item': menu_item_details,
            'quantity': order_item.quantity,
            'unit_price': str(order_item.unit_price),
            'subtotal': str(order_item.subtotal),
            'notes': getattr(order_item, 'notes', ''),
            'customizations': customizations
        }
        
        items.append(item_data)
    
    return items

def serialize_menu_item_images(images, size='medium'):
    """Serialize menu item images with size options"""
    image_data = []
    
    for image in images:
        # Handle different image sizes if you have them
        image_url = image.image.url
        
        # If you have multiple sizes stored, adjust the URL based on size parameter
        if hasattr(image, f'image_{size}') and getattr(image, f'image_{size}'):
            image_url = getattr(image, f'image_{size}').url
        
        image_data.append({
            'id': image.id,
            'url': image_url,
            'alt_text': getattr(image, 'alt_text', ''),
            'is_primary': getattr(image, 'is_primary', False)
        })
    
    # Sort by primary first, then by creation order
    image_data.sort(key=lambda x: (not x['is_primary'], x['id']))
    
    return image_data

def serialize_driver_info(driver, include_location=True):
    """Serialize driver information with optional location"""
    driver_profile = getattr(driver, 'driverprofile', None)
    
    driver_data = {
        'id': driver.id,
        'full_name': driver.full_name,
        'phone': getattr(driver, 'phone', ''),
        'vehicle_info': driver_profile.vehicle_info if driver_profile else ''
    }
    
    if include_location:
        # Get latest driver location
        latest_location = driver.driverlocation_set.order_by('-timestamp').first()
        if latest_location:
            driver_data['current_location'] = {
                'lat': float(latest_location.latitude),
                'lng': float(latest_location.longitude)
            }
    
    return driver_data

def calculate_subtotal(order_items):
    """Calculate order subtotal"""
    subtotal = sum(item.subtotal for item in order_items)
    return str(subtotal)

def calculate_tax(order):
    """Calculate tax for order"""
    if hasattr(order, 'tax') and order.tax:
        return str(order.tax)
    
    # Calculate tax if not stored (e.g., 8% tax rate)
    subtotal = sum(item.subtotal for item in order.items.all())
    tax_rate = Decimal('0.08')  # Adjust based on your tax calculation
    tax = subtotal * tax_rate
    return str(tax.quantize(Decimal('0.01')))

# URL Configuration (add to your urls.py)
"""
from django.urls import path
from .views import order_details_enhanced

urlpatterns = [
    # ... your existing URLs
    path('api/orders/<str:order_id>/details/', order_details_enhanced, name='order_details_enhanced'),
]
"""

# Alternative Class-Based View Implementation
# from rest_framework.views import APIView

# class OrderDetailsEnhancedView(APIView):
#     permission_classes = [IsAuthenticated]
    
#     def get(self, request, order_id):
#         """Get enhanced order details"""
#         return order_details_enhanced(request, order_id)

# # ViewSet Implementation (if you prefer DRF ViewSets)
# from rest_framework import viewsets
# from rest_framework.decorators import action

# class OrderViewSet(viewsets.ModelViewSet):
#     # ... your existing order viewset code
    
#     @action(detail=True, methods=['get'], url_path='details')
#     def enhanced_details(self, request, pk=None):
#         """Get enhanced order details with full information"""
#         return order_details_enhanced(request, pk)