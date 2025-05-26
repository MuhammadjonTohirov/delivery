# webapp/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from restaurants.models import Restaurant, MenuItem, MenuCategory
from orders.models import Order
from users.models import CustomUser
import uuid

def home(request):
    """Home page view"""
    return render(request, 'home.html')

def login_view(request):
    """Login page view"""
    if request.user.is_authenticated:
        return redirect('webapp:dashboard')
    return render(request, 'login.html')

def register_view(request):
    """Registration page view"""
    if request.user.is_authenticated:
        return redirect('webapp:dashboard')
    return render(request, 'register.html')

@login_required
def profile_view(request):
    """User profile page view"""
    return render(request, 'profile.html')

@login_required
def dashboard_view(request):
    """Main dashboard redirect based on user role"""
    user = request.user
    
    if user.role == 'CUSTOMER':
        return redirect('webapp:customer_dashboard')
    elif user.role == 'RESTAURANT':
        return redirect('webapp:restaurant_dashboard')
    elif user.role == 'DRIVER':
        return redirect('webapp:driver_dashboard')
    elif user.role == 'ADMIN':
        return redirect('webapp:restaurant_dashboard')  # Admin can access restaurant dashboard
    else:
        return redirect('webapp:home')

@login_required
def customer_dashboard(request):
    """Customer dashboard view"""
    if request.user.role not in ['CUSTOMER', 'ADMIN']:
        return redirect('webapp:home')
    
    return render(request, 'dashboards/customer_dashboard.html')

@login_required
def restaurant_dashboard(request):
    """Restaurant dashboard view - Modern UI"""
    if request.user.role not in ['RESTAURANT', 'ADMIN']:
        return redirect('webapp:home')
    
    context = {
        'user': request.user,
        'page_title': 'Restaurant Dashboard'
    }
    
    return render(request, 'dashboards/modern_restaurant_dashboard.html', context)

@login_required
def driver_dashboard(request):
    """Driver dashboard view"""
    if request.user.role not in ['DRIVER', 'ADMIN']:
        return redirect('webapp:home')
    
    return render(request, 'dashboards/driver_dashboard.html')

def restaurant_list(request):
    """List all restaurants"""
    return render(request, 'restaurants/restaurant_list.html')

def restaurant_detail(request, restaurant_id):
    """Restaurant detail view with menu"""
    try:
        restaurant = Restaurant.objects.get(id=restaurant_id)
    except Restaurant.DoesNotExist:
        messages.error(request, 'Restaurant not found.')
        return redirect('webapp:restaurant_list')
    
    context = {
        'restaurant': restaurant,
        'restaurant_id': restaurant_id
    }
    return render(request, 'restaurants/restaurant_detail.html', context)

@login_required
def customer_order_list(request):
    """Customer's order history"""
    if request.user.role not in ['CUSTOMER', 'ADMIN']:
        return redirect('webapp:home')
    
    orders = Order.objects.filter(customer=request.user).order_by('-created_at')
    
    # Pagination
    paginator = Paginator(orders, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'orders': page_obj,
        'page_obj': page_obj
    }
    return render(request, 'orders/customer_order_list.html', context)

@login_required
def manage_restaurant(request):
    """Manage restaurant details"""
    if request.user.role not in ['RESTAURANT', 'ADMIN']:
        return redirect('webapp:home')
    
    return render(request, 'restaurants/manage_restaurant.html')

@login_required
def restaurant_orders(request):
    """Restaurant order management"""
    if request.user.role not in ['RESTAURANT', 'ADMIN']:
        return redirect('webapp:home')
    
    return render(request, 'restaurants/restaurant_orders.html')

@login_required
def menu_management(request):
    """Menu management page"""
    if request.user.role not in ['RESTAURANT', 'ADMIN']:
        return redirect('webapp:home')
    
    return render(request, 'restaurants/manage_menu.html')

@login_required
def menu_category_create(request):
    """Create new menu category"""
    if request.user.role not in ['RESTAURANT', 'ADMIN']:
        return redirect('webapp:home')
    
    context = {
        'form_type': 'Add New Category',
        'category_id': None
    }
    return render(request, 'restaurants/category_form.html', context)

@login_required
def menu_category_edit(request, category_id):
    """Edit menu category"""
    if request.user.role not in ['RESTAURANT', 'ADMIN']:
        return redirect('webapp:home')
    
    try:
        category = MenuCategory.objects.get(id=category_id)
        # Check if user owns this category's restaurant
        if request.user.role == 'RESTAURANT' and category.restaurant.user != request.user:
            messages.error(request, 'You can only edit your own categories.')
            return redirect('webapp:menu_management')
    except MenuCategory.DoesNotExist:
        messages.error(request, 'Category not found.')
        return redirect('webapp:menu_management')
    
    context = {
        'form_type': 'Edit Category',
        'category_id': category_id,
        'category': category
    }
    return render(request, 'restaurants/category_form.html', context)

@login_required
def menu_item_create(request, category_id=None):
    """Create new menu item"""
    if request.user.role not in ['RESTAURANT', 'ADMIN']:
        return redirect('webapp:home')
    
    context = {
        'form_type': 'Add New Menu Item',
        'item_id': None,
        'category_id': category_id
    }
    return render(request, 'restaurants/menu_item_form.html', context)

@login_required
def menu_item_edit(request, item_id):
    """Edit menu item"""
    if request.user.role not in ['RESTAURANT', 'ADMIN']:
        return redirect('webapp:home')
    
    try:
        item = MenuItem.objects.get(id=item_id)
        # Check if user owns this item's restaurant
        if request.user.role == 'RESTAURANT' and item.restaurant.user != request.user:
            messages.error(request, 'You can only edit your own menu items.')
            return redirect('webapp:menu_management')
    except MenuItem.DoesNotExist:
        messages.error(request, 'Menu item not found.')
        return redirect('webapp:menu_management')
    
    context = {
        'form_type': 'Edit Menu Item',
        'item_id': item_id,
        'item': item
    }
    return render(request, 'restaurants/menu_item_form.html', context)

@login_required
def driver_task_list(request):
    """Driver task list"""
    if request.user.role not in ['DRIVER', 'ADMIN']:
        return redirect('webapp:home')
    
    return render(request, 'drivers/task_list.html')

@login_required
def driver_earnings_report(request):
    """Driver earnings report"""
    if request.user.role not in ['DRIVER', 'ADMIN']:
        return redirect('webapp:home')
    
    return render(request, 'drivers/earnings_report.html')

# API-like views for AJAX requests (optional, can use DRF instead)
@login_required
@require_http_methods(["GET"])
def api_restaurant_stats(request, restaurant_id):
    """Get restaurant statistics for dashboard"""
    if request.user.role not in ['RESTAURANT', 'ADMIN']:
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    try:
        restaurant = Restaurant.objects.get(id=restaurant_id)
        if request.user.role == 'RESTAURANT' and restaurant.user != request.user:
            return JsonResponse({'error': 'Permission denied'}, status=403)
        
        # Get statistics
        total_orders = Order.objects.filter(restaurant=restaurant).count()
        delivered_orders = Order.objects.filter(restaurant=restaurant, status='DELIVERED').count()
        cancelled_orders = Order.objects.filter(restaurant=restaurant, status='CANCELLED').count()
        
        # Calculate revenue (simplified)
        total_revenue = sum(
            order.total_price for order in Order.objects.filter(
                restaurant=restaurant, 
                status='DELIVERED'
            )
        )
        
        stats = {
            'total_orders': total_orders,
            'delivered_orders': delivered_orders,
            'cancelled_orders': cancelled_orders,
            'total_revenue': float(total_revenue),
            'restaurant_name': restaurant.name
        }
        
        return JsonResponse(stats)
        
    except Restaurant.DoesNotExist:
        return JsonResponse({'error': 'Restaurant not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)