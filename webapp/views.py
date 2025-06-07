from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
import json


def index(request):
    """
    API index page with documentation links
    """
    return render(request, 'index.html')


# Keep minimal AJAX endpoints for backwards compatibility
@csrf_exempt
@login_required
def ajax_update_order_status(request):
    """
    AJAX endpoint to update order status
    """
    if request.method == 'POST' and request.user.role == 'RESTAURANT':
        try:
            from orders.models import Order
            
            data = json.loads(request.body)
            order_id = data.get('order_id')
            new_status = data.get('status')
            
            order = Order.objects.get(id=order_id, restaurant=request.user.restaurant)
            order.status = new_status
            order.save()
            
            return JsonResponse({'success': True, 'message': 'Order status updated'})
        
        except (Order.DoesNotExist, json.JSONDecodeError, KeyError):
            return JsonResponse({'success': False, 'message': 'Invalid request'})
    
    return JsonResponse({'success': False, 'message': 'Method not allowed'})


@csrf_exempt
@login_required
def ajax_driver_update_location(request):
    """
    AJAX endpoint for driver location updates
    """
    if request.method == 'POST' and request.user.role == 'DRIVER':
        try:
            from drivers.models import DriverLocation
            
            data = json.loads(request.body)
            latitude = data.get('latitude')
            longitude = data.get('longitude')
            
            # Save location to database
            DriverLocation.objects.create(
                driver=request.user.driver_profile,
                latitude=latitude,
                longitude=longitude
            )
            
            return JsonResponse({'success': True, 'message': 'Location updated'})
        
        except (json.JSONDecodeError, KeyError):
            return JsonResponse({'success': False, 'message': 'Invalid request'})
    
    return JsonResponse({'success': False, 'message': 'Method not allowed'})
