from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
import json

from users.models import CustomUser
from restaurants.models import Restaurant
from orders.models import Order


def home(request):
    """
    Home page view
    """
    return render(request, 'home.html')


def login_view(request):
    """
    Login page view
    """
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        user = authenticate(request, username=email, password=password)
        if user is not None:
            login(request, user)
            
            # Redirect based on user role
            if user.role == 'RESTAURANT':
                return redirect('webapp:restaurant_dashboard')
            elif user.role == 'DRIVER':
                return redirect('webapp:driver_dashboard')
            elif user.role == 'CUSTOMER':
                return redirect('webapp:customer_dashboard')
            elif user.role == 'ADMIN':
                return redirect('webapp:admin_dashboard')
            else:
                return redirect('webapp:home')
        else:
            messages.error(request, 'Invalid email or password')
    
    return render(request, 'login.html')


def logout_view(request):
    """
    Logout view
    """
    logout(request)
    return redirect('webapp:home')


@login_required
def profile_view(request):
    """
    User profile view
    """
    return render(request, 'profile.html', {'user': request.user})


class RestaurantDashboardView(LoginRequiredMixin, TemplateView):
    """
    Restaurant dashboard view
    """
    template_name = 'dashboards/restaurant_dashboard_new.html'
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.role == 'RESTAURANT':
            messages.error(request, 'Access denied. Restaurant account required.')
            return redirect('webapp:home')
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Get restaurant data
        try:
            restaurant = user.restaurant
            context['restaurant'] = restaurant
            
            # Get recent orders
            recent_orders = Order.objects.filter(restaurant=restaurant).order_by('-created_at')[:10]
            context['recent_orders'] = recent_orders
            
            # Get basic stats
            context['stats'] = {
                'total_orders': Order.objects.filter(restaurant=restaurant).count(),
                'pending_orders': Order.objects.filter(restaurant=restaurant, status='PLACED').count(),
                'menu_items': restaurant.menu_items.count(),
            }
        except AttributeError:
            context['restaurant'] = None
            messages.warning(self.request, 'No restaurant profile found. Please contact support.')
        
        return context


class CustomerDashboardView(LoginRequiredMixin, TemplateView):
    """
    Customer dashboard view
    """
    template_name = 'dashboards/customer_dashboard.html'
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.role == 'CUSTOMER':
            messages.error(request, 'Access denied. Customer account required.')
            return redirect('webapp:home')
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Get customer orders
        recent_orders = Order.objects.filter(customer=user).order_by('-created_at')[:5]
        context['recent_orders'] = recent_orders
        
        # Get favorite restaurants (based on order history)
        favorite_restaurants = Restaurant.objects.filter(
            orders__customer=user
        ).distinct()[:5]
        context['favorite_restaurants'] = favorite_restaurants
        
        return context


class DriverDashboardView(LoginRequiredMixin, TemplateView):
    """
    Driver dashboard view
    """
    template_name = 'dashboards/driver_dashboard.html'
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.role == 'DRIVER':
            messages.error(request, 'Access denied. Driver account required.')
            return redirect('webapp:home')
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Get driver data
        try:
            driver_profile = user.driver_profile
            context['driver_profile'] = driver_profile
            
            # Get active tasks
            from drivers.models import DriverTask
            active_tasks = DriverTask.objects.filter(
                driver=driver_profile,
                status__in=['PENDING', 'ACCEPTED', 'PICKED_UP']
            ).order_by('-assigned_at')
            context['active_tasks'] = active_tasks
            
            # Get recent earnings
            recent_earnings = driver_profile.earnings.order_by('-timestamp')[:10]
            context['recent_earnings'] = recent_earnings
            
        except AttributeError:
            context['driver_profile'] = None
            messages.warning(self.request, 'No driver profile found. Please contact support.')
        
        return context


@login_required
def restaurant_orders_view(request):
    """
    Restaurant orders management view
    """
    if request.user.role != 'RESTAURANT':
        messages.error(request, 'Access denied.')
        return redirect('webapp:home')
    
    try:
        restaurant = request.user.restaurant
        orders = Order.objects.filter(restaurant=restaurant).order_by('-created_at')
        
        # Filter by status if provided
        status_filter = request.GET.get('status')
        if status_filter:
            orders = orders.filter(status=status_filter)
        
        context = {
            'restaurant': restaurant,
            'orders': orders,
            'status_filter': status_filter,
        }
        return render(request, 'restaurants/restaurant_orders.html', context)
    
    except AttributeError:
        messages.error(request, 'No restaurant profile found.')
        return redirect('webapp:restaurant_dashboard')


@login_required
def restaurant_menu_view(request):
    """
    Restaurant menu management view
    """
    if request.user.role != 'RESTAURANT':
        messages.error(request, 'Access denied.')
        return redirect('webapp:home')
    
    try:
        restaurant = request.user.restaurant
        menu_items = restaurant.menu_items.all().order_by('category', 'name')
        categories = restaurant.menu_categories.all().order_by('order', 'name')
        
        context = {
            'restaurant': restaurant,
            'menu_items': menu_items,
            'categories': categories,
        }
        return render(request, 'restaurants/manage_menu.html', context)
    
    except AttributeError:
        messages.error(request, 'No restaurant profile found.')
        return redirect('webapp:restaurant_dashboard')


@login_required
def customer_orders_view(request):
    """
    Customer order history view
    """
    if request.user.role != 'CUSTOMER':
        messages.error(request, 'Access denied.')
        return redirect('webapp:home')
    
    orders = Order.objects.filter(customer=request.user).order_by('-created_at')
    
    context = {
        'orders': orders,
    }
    return render(request, 'orders/customer_order_list.html', context)


@login_required
def driver_tasks_view(request):
    """
    Driver tasks view
    """
    if request.user.role != 'DRIVER':
        messages.error(request, 'Access denied.')
        return redirect('webapp:home')
    
    try:
        driver_profile = request.user.driver_profile
        from drivers.models import DriverTask
        
        tasks = DriverTask.objects.filter(driver=driver_profile).order_by('-assigned_at')
        
        context = {
            'driver_profile': driver_profile,
            'tasks': tasks,
        }
        return render(request, 'drivers/task_list.html', context)
    
    except AttributeError:
        messages.error(request, 'No driver profile found.')
        return redirect('webapp:driver_dashboard')


@login_required
def driver_earnings_view(request):
    """
    Driver earnings view
    """
    if request.user.role != 'DRIVER':
        messages.error(request, 'Access denied.')
        return redirect('webapp:home')
    
    try:
        driver_profile = request.user.driver_profile
        earnings = driver_profile.earnings.order_by('-timestamp')
        
        context = {
            'driver_profile': driver_profile,
            'earnings': earnings,
        }
        return render(request, 'drivers/earnings_report.html', context)
    
    except AttributeError:
        messages.error(request, 'No driver profile found.')
        return redirect('webapp:driver_dashboard')


def restaurant_list_view(request):
    """
    Public restaurant list view
    """
    restaurants = Restaurant.objects.filter(is_open=True)
    
    # Filter by search query
    search_query = request.GET.get('search')
    if search_query:
        restaurants = restaurants.filter(name__icontains=search_query)
    
    context = {
        'restaurants': restaurants,
        'search_query': search_query,
    }
    return render(request, 'restaurants/restaurant_list.html', context)


def restaurant_detail_view(request, restaurant_id):
    """
    Restaurant detail view with menu
    """
    try:
        restaurant = Restaurant.objects.get(id=restaurant_id)
        menu_categories = restaurant.menu_categories.prefetch_related('items').order_by('order', 'name')
        
        context = {
            'restaurant': restaurant,
            'menu_categories': menu_categories,
        }
        return render(request, 'restaurants/restaurant_detail.html', context)
    
    except Restaurant.DoesNotExist:
        messages.error(request, 'Restaurant not found.')
        return redirect('webapp:restaurant_list')


# API endpoints for AJAX calls
@csrf_exempt
@login_required
def ajax_update_order_status(request):
    """
    AJAX endpoint to update order status
    """
    if request.method == 'POST' and request.user.role == 'RESTAURANT':
        try:
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
            data = json.loads(request.body)
            latitude = data.get('latitude')
            longitude = data.get('longitude')
            
            # Save location to database
            from drivers.models import DriverLocation
            DriverLocation.objects.create(
                driver=request.user.driver_profile,
                latitude=latitude,
                longitude=longitude
            )
            
            return JsonResponse({'success': True, 'message': 'Location updated'})
        
        except (json.JSONDecodeError, KeyError):
            return JsonResponse({'success': False, 'message': 'Invalid request'})
    
    return JsonResponse({'success': False, 'message': 'Method not allowed'})


def register_view(request):
    """
    User registration view
    """
    if request.method == 'POST':
        # Handle registration form
        email = request.POST.get('email')
        password = request.POST.get('password')
        full_name = request.POST.get('full_name')
        role = request.POST.get('role', 'CUSTOMER')
        
        try:
            # Create user
            user = CustomUser.objects.create_user(
                email=email,
                password=password,
                full_name=full_name,
                role=role
            )
            
            messages.success(request, 'Account created successfully! Please log in.')
            return redirect('webapp:login')
        
        except Exception as e:
            messages.error(request, f'Registration failed: {str(e)}')
    
    return render(request, 'register.html')


@login_required
def admin_dashboard_view(request):
    """
    Admin dashboard view
    """
    if not request.user.is_staff and request.user.role != 'ADMIN':
        messages.error(request, 'Access denied. Admin privileges required.')
        return redirect('webapp:home')
    
    # Get platform statistics
    total_users = CustomUser.objects.count()
    total_restaurants = Restaurant.objects.count()
    total_orders = Order.objects.count()
    pending_orders = Order.objects.filter(status='PLACED').count()
    
    # Recent activity
    recent_orders = Order.objects.order_by('-created_at')[:10]
    recent_users = CustomUser.objects.order_by('-date_joined')[:10]
    
    context = {
        'stats': {
            'total_users': total_users,
            'total_restaurants': total_restaurants,
            'total_orders': total_orders,
            'pending_orders': pending_orders,
        },
        'recent_orders': recent_orders,
        'recent_users': recent_users,
    }
    
    return render(request, 'dashboards/admin_dashboard.html', context)
