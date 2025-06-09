import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
import datetime
import uuid
from decimal import Decimal

from users.models import CustomUser, CustomerProfile, DriverProfile, RestaurantProfile
from restaurants.models import Restaurant, MenuItem, MenuCategory
from orders.models import Order, OrderItem
from drivers.models import DriverTask, DriverAvailability, DriverLocation, DriverEarning

# Fixtures for the complete platform integration tests

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def create_users(db):
    """Create a set of users for integration testing."""
    customer = CustomUser.objects.create_user(
        email='customer@example.com',
        full_name='Test Customer',
        password='testpassword123',
        role='CUSTOMER'
    )
    CustomerProfile.objects.create(
        user=customer,
        default_address='123 Test St, Test City',
        default_location_lat=40.7128,
        default_location_lng=-74.0060
    )
    
    restaurant_owner = CustomUser.objects.create_user(
        email='restaurant@example.com',
        full_name='Test Restaurant Owner',
        password='testpassword123',
        role='RESTAURANT'
    )
    restaurant_profile = RestaurantProfile.objects.create(
        user=restaurant_owner,
        business_name='Test Restaurant',
        business_address='456 Food St, Test City',
        business_registration_number='BR12345'
    )
    
    driver = CustomUser.objects.create_user(
        email='driver@example.com',
        full_name='Test Driver',
        password='testpassword123',
        role='DRIVER'
    )
    driver_profile = DriverProfile.objects.create(
        user=driver,
        vehicle_type='Car',
        license_number='DL12345'
    )
    
    admin = CustomUser.objects.create_superuser(
        email='admin@example.com',
        full_name='Test Admin',
        password='testpassword123',
        role='ADMIN'
    )
    
    return {
        'customer': customer,
        'restaurant_owner': restaurant_owner,
        'driver': driver,
        'admin': admin
    }

@pytest.fixture
def get_auth_token(api_client):
    """Get authentication token for a user."""
    def _get_token(email, password):
        url = reverse('users:token_obtain_pair')
        response = api_client.post(url, {'email': email, 'password': password}, format='json')
        return response.data.get('access')
    return _get_token

@pytest.fixture
def auth_client(api_client, get_auth_token):
    """Get authenticated client for a user."""
    def get_auth_client(user=None, email=None, password=None):
        client = APIClient()
        
        if user:
            email = user.email
            password = 'testpassword123'  # Default test password
        
        if email and password:
            token = get_auth_token(email, password)
            client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        return client
    return get_auth_client

@pytest.fixture
def setup_restaurant(db, create_users):
    """Set up a restaurant with menu items."""
    restaurant_owner = create_users['restaurant_owner']
    
    # Create restaurant
    restaurant = Restaurant.objects.create(
        user=restaurant_owner,
        name='Test Restaurant',
        address='456 Food St, Test City',
        description='A test restaurant',
        is_open=True
    )
    
    # Create menu categories (now global)
    category1, created = MenuCategory.objects.get_or_create(
        name='Main Dishes',
        defaults={'description': 'Main course items'}
    )
    
    category2, created = MenuCategory.objects.get_or_create(
        name='Desserts',
        defaults={'description': 'Sweet treats'}
    )
    
    # Create menu items
    item1 = MenuItem.objects.create(
        restaurant=restaurant,
        category=category1,
        name='Burger',
        description='Delicious burger with fries',
        price=Decimal('10.99'),
        is_available=True
    )
    
    item2 = MenuItem.objects.create(
        restaurant=restaurant,
        category=category1,
        name='Pizza',
        description='Margherita pizza',
        price=Decimal('12.99'),
        is_available=True
    )
    
    item3 = MenuItem.objects.create(
        restaurant=restaurant,
        category=category2,
        name='Ice Cream',
        description='Vanilla ice cream',
        price=Decimal('4.99'),
        is_available=True
    )
    
    return {
        'restaurant': restaurant,
        'categories': [category1, category2],
        'menu_items': [item1, item2, item3]
    }

@pytest.fixture
def setup_driver(db, create_users):
    """Set up a driver with availability."""
    driver = create_users['driver']
    
    # Create driver availability
    availability = DriverAvailability.objects.create(
        driver=driver.driver_profile,
        status='AVAILABLE'
    )
    
    # Create driver location
    location = DriverLocation.objects.create(
        driver=driver.driver_profile,
        latitude=Decimal('40.7128'),
        longitude=Decimal('-74.0060')
    )
    
    return {
        'driver': driver,
        'availability': availability,
        'location': location
    }

# Integration tests for the complete order flow

@pytest.mark.django_db
class TestCompleteOrderFlow:
    
    def test_complete_order_flow(self, create_users, setup_restaurant, setup_driver, auth_client):
        """Test the complete flow from order creation to delivery."""
        # Set up users and clients
        customer = create_users['customer']
        restaurant_owner = create_users['restaurant_owner']
        driver = create_users['driver']
        
        customer_client = auth_client(user=customer)
        restaurant_client = auth_client(user=restaurant_owner)
        driver_client = auth_client(user=driver)
        
        restaurant = setup_restaurant['restaurant']
        menu_items = setup_restaurant['menu_items']
        
        # Step 1: Customer creates an order
        order_data = {
            'restaurant': str(restaurant.id),
            'delivery_address': '123 Test St, Test City',
            'delivery_lat': '40.7128',
            'delivery_lng': '-74.0060',
            'delivery_fee': '2.50',
            'notes': 'Please deliver quickly.',
            'items': [
                {
                    'menu_item': str(menu_items[0].id),
                    'quantity': 2,
                    'notes': 'Extra ketchup.'
                },
                {
                    'menu_item': str(menu_items[2].id),
                    'quantity': 1,
                    'notes': ''
                }
            ]
        }
        
        url = reverse('order-list')
        response = customer_client.post(url, order_data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        order_id = response.data['id']
        
        # Step 2: Restaurant owner views the order
        url = reverse('order-detail', args=[order_id])
        response = restaurant_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == 'PLACED'
        
        # Step 3: Restaurant owner accepts the order
        url = reverse('order-restaurant-action', args=[order_id])
        response = restaurant_client.post(url, {'action': 'accept', 'note': 'Order accepted.'}, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == 'CONFIRMED'
        
        # Step 4: Restaurant owner marks order as preparing
        url = reverse('order-preparing', args=[order_id])
        response = restaurant_client.post(url, {'note': 'Order is being prepared.'}, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == 'PREPARING'
        
        # Step 5: Restaurant owner marks order as ready for pickup
        url = reverse('order-ready-for-pickup', args=[order_id])
        response = restaurant_client.post(url, {'note': 'Order is ready for pickup.'}, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == 'READY_FOR_PICKUP'
        
        # Step 6: Admin assigns the order to a driver (in a real system, this might be automated)
        admin_client = auth_client(email='admin@example.com', password='testpassword123')
        
        driver_task_data = {
            'driver': str(driver.driver_profile.id),
            'order': order_id,
            'status': 'PENDING',
            'notes': 'Please pick up from the restaurant.'
        }
        
        url = reverse('driver-task-list')
        response = admin_client.post(url, driver_task_data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        task_id = response.data['id']
        
        # Step 7: Driver accepts the task
        url = reverse('driver-task-accept', args=[task_id])
        response = driver_client.post(url, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == 'ACCEPTED'
        
        # Step 8: Driver marks task as picked up
        url = reverse('driver-task-picked-up', args=[task_id])
        response = driver_client.post(url, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == 'PICKED_UP'
        
        # Verify order status is updated
        url = reverse('order-detail', args=[order_id])
        response = customer_client.get(url)
        assert response.data['status'] == 'ON_THE_WAY'
        
        # Step 9: Driver marks task as delivered
        url = reverse('driver-task-delivered', args=[task_id])
        response = driver_client.post(url, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == 'DELIVERED'
        
        # Verify order status is updated to delivered
        url = reverse('order-detail', args=[order_id])
        response = customer_client.get(url)
        assert response.data['status'] == 'DELIVERED'
        
        # Step 10: Verify driver earnings were created
        url = reverse('driver-earning-list')
        response = driver_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) > 0
        
        # Step 11: Customer can view order history
        url = reverse('order-history', args=[order_id])
        response = customer_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) > 0  # Should have multiple status updates
    
    def test_restaurant_rejects_order(self, create_users, setup_restaurant, auth_client):
        """Test flow when restaurant rejects an order."""
        # Set up users and clients
        customer = create_users['customer']
        restaurant_owner = create_users['restaurant_owner']
        
        customer_client = auth_client(user=customer)
        restaurant_client = auth_client(user=restaurant_owner)
        
        restaurant = setup_restaurant['restaurant']
        menu_items = setup_restaurant['menu_items']
        
        # Step 1: Customer creates an order
        order_data = {
            'restaurant': str(restaurant.id),
            'delivery_address': '123 Test St, Test City',
            'delivery_lat': '40.7128',
            'delivery_lng': '-74.0060',
            'delivery_fee': '2.50',
            'notes': 'Please deliver quickly.',
            'items': [
                {
                    'menu_item': str(menu_items[0].id),
                    'quantity': 2,
                    'notes': 'Extra ketchup.'
                }
            ]
        }
        
        url = reverse('order-list')
        response = customer_client.post(url, order_data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        order_id = response.data['id']
        
        # Step 2: Restaurant owner rejects the order
        url = reverse('order-restaurant-action', args=[order_id])
        response = restaurant_client.post(
            url, 
            {'action': 'reject', 'note': 'Item out of stock.'}, 
            format='json'
        )
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == 'CANCELLED'
        
        # Step 3: Customer can see the cancelled order
        url = reverse('order-detail', args=[order_id])
        response = customer_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == 'CANCELLED'
    
    def test_customer_views_restaurant_and_menu(self, create_users, setup_restaurant, auth_client):
        """Test customer browsing restaurants and menus."""
        customer = create_users['customer']
        customer_client = auth_client(user=customer)
        
        # Step 1: Customer views all restaurants
        url = reverse('restaurant-list')
        response = customer_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) > 0
        
        restaurant_id = response.data['results'][0]['id']
        
        # Step 2: Customer views a specific restaurant
        url = reverse('restaurant-detail', args=[restaurant_id])
        response = customer_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        
        # Step 3: Customer views restaurant menu
        url = reverse('restaurant-menu', args=[restaurant_id])
        response = customer_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) > 0  # Should have menu categories
    
    def test_driver_manages_availability(self, create_users, auth_client):
        """Test driver updating availability status."""
        driver = create_users['driver']
        driver_client = auth_client(user=driver)
        
        # Step 1: Driver goes online
        url = reverse('driver-availability-go-online')
        response = driver_client.post(url, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == 'AVAILABLE'
        
        # Step 2: Driver goes offline
        url = reverse('driver-availability-go-offline')
        response = driver_client.post(url, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == 'OFFLINE'
        
        # Step 3: Driver updates location
        location_data = {
            'latitude': '40.7128',
            'longitude': '-74.0060',
            'accuracy': 10.0
        }
        
        url = reverse('driver-location-list')
        response = driver_client.post(url, location_data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
    
    def test_driver_earnings_summary(self, create_users, setup_restaurant, setup_driver, auth_client):
        """Test driver earnings summary functionality."""
        # Set up users and clients
        customer = create_users['customer']
        restaurant_owner = create_users['restaurant_owner']
        driver = create_users['driver']
        admin = create_users['admin']
        
        customer_client = auth_client(user=customer)
        restaurant_client = auth_client(user=restaurant_owner)
        driver_client = auth_client(user=driver)
        admin_client = auth_client(user=admin)
        
        restaurant = setup_restaurant['restaurant']
        menu_items = setup_restaurant['menu_items']
        
        # Create and complete an order
        # Step 1: Customer creates an order
        order_data = {
            'restaurant': str(restaurant.id),
            'delivery_address': '123 Test St, Test City',
            'delivery_lat': '40.7128',
            'delivery_lng': '-74.0060',
            'delivery_fee': '2.50',
            'notes': 'Please deliver quickly.',
            'items': [
                {
                    'menu_item': str(menu_items[0].id),
                    'quantity': 1
                }
            ]
        }
        
        url = reverse('order-list')
        response = customer_client.post(url, order_data, format='json')
        order_id = response.data['id']
        
        # Step 2: Restaurant accepts order
        url = reverse('order-restaurant-action', args=[order_id])
        restaurant_client.post(url, {'action': 'accept'}, format='json')
        
        url = reverse('order-preparing', args=[order_id])
        restaurant_client.post(url, format='json')
        
        url = reverse('order-ready-for-pickup', args=[order_id])
        restaurant_client.post(url, format='json')
        
        # Step 3: Admin assigns task to driver
        driver_task_data = {
            'driver': str(driver.driver_profile.id),
            'order': order_id,
            'status': 'PENDING'
        }
        
        url = reverse('driver-task-list')
        response = admin_client.post(url, driver_task_data, format='json')
        task_id = response.data['id']
        
        # Step 4: Driver completes the delivery
        url = reverse('driver-task-accept', args=[task_id])
        driver_client.post(url, format='json')
        
        url = reverse('driver-task-picked-up', args=[task_id])
        driver_client.post(url, format='json')
        
        url = reverse('driver-task-delivered', args=[task_id])
        driver_client.post(url, format='json')
        
        # Step 5: Driver views earnings summary
        url = reverse('driver-earning-summary')
        response = driver_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['total_earnings'] > 0
        assert response.data['total_deliveries'] > 0


@pytest.mark.django_db
class TestRestaurantManagement:
    
    def test_restaurant_menu_management(self, create_users, setup_restaurant, auth_client):
        """Test restaurant owner managing menu items."""
        restaurant_owner = create_users['restaurant_owner']
        restaurant_client = auth_client(user=restaurant_owner)
        
        restaurant = setup_restaurant['restaurant']
        category = setup_restaurant['categories'][0]
        
        # Step 1: Restaurant owner adds a new menu item
        menu_item_data = {
            'restaurant': str(restaurant.id),
            'category': str(category.id),
            'name': 'Pasta',
            'description': 'Delicious pasta with tomato sauce',
            'price': '9.99',
            'is_available': True
        }
        
        url = reverse('menu-item-list')
        response = restaurant_client.post(url, menu_item_data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        item_id = response.data['id']
        
        # Step 2: Restaurant owner updates a menu item
        update_data = {
            'price': '11.99',
            'description': 'Delicious pasta with creamy sauce'
        }
        
        url = reverse('menu-item-detail', args=[item_id])
        response = restaurant_client.patch(url, update_data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert Decimal(response.data['price']) == Decimal('11.99')
        assert response.data['description'] == update_data['description']
        
        # Step 3: Restaurant owner toggles item availability
        update_data = {
            'is_available': False
        }
        
        url = reverse('menu-item-detail', args=[item_id])
        response = restaurant_client.patch(url, update_data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['is_available'] == False
    
    def test_restaurant_profile_management(self, create_users, auth_client):
        """Test restaurant owner managing restaurant profile."""
        restaurant_owner = create_users['restaurant_owner']
        restaurant_client = auth_client(user=restaurant_owner)
        
        # Step 1: Restaurant owner creates a restaurant
        restaurant_data = {
            'name': 'New Restaurant',
            'address': '789 Food Ave, Test City',
            'description': 'A new restaurant',
            'is_open': True,
            'opening_time': '08:00:00',
            'closing_time': '22:00:00'
        }
        
        url = reverse('restaurant-list')
        response = restaurant_client.post(url, restaurant_data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        restaurant_id = response.data['id']
        
        # Step 2: Restaurant owner updates restaurant profile
        update_data = {
            'description': 'An updated restaurant description',
            'is_open': False
        }
        
        url = reverse('restaurant-detail', args=[restaurant_id])
        response = restaurant_client.patch(url, update_data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['description'] == update_data['description']
        assert response.data['is_open'] == update_data['is_open']


@pytest.mark.django_db
class TestRoleBasedAccessControl:
    
    def test_customer_cannot_access_restaurant_functions(self, create_users, setup_restaurant, auth_client):
        """Test customers cannot access restaurant owner functions."""
        customer = create_users['customer']
        customer_client = auth_client(user=customer)
        
        # Try to create a restaurant
        restaurant_data = {
            'name': 'Unauthorized Restaurant',
            'address': '111 Fake St, Test City',
            'is_open': True
        }
        
        url = reverse('restaurant-list')
        response = customer_client.post(url, restaurant_data, format='json')
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
        
        # Try to access restaurant owner profile
        url = reverse('restaurant-detail', args=[setup_restaurant['restaurant'].id])
        response = customer_client.patch(url, {'is_open': False}, format='json')
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_customer_cannot_access_driver_functions(self, create_users, setup_driver, auth_client):
        """Test customers cannot access driver functions."""
        customer = create_users['customer']
        customer_client = auth_client(user=customer)
        
        # Try to update driver availability
        url = reverse('driver-availability-go-online')
        response = customer_client.post(url, format='json')
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
        
        # Try to access driver earnings
        url = reverse('driver-earning-list')
        response = customer_client.get(url)
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_driver_cannot_access_restaurant_functions(self, create_users, setup_restaurant, auth_client):
        """Test drivers cannot access restaurant owner functions."""
        driver = create_users['driver']
        driver_client = auth_client(user=driver)
        
        # Try to create a menu item
        menu_item_data = {
            'restaurant': str(setup_restaurant['restaurant'].id),
            'category': str(setup_restaurant['categories'][0].id),
            'name': 'Unauthorized Item',
            'price': '9.99',
            'is_available': True
        }
        
        url = reverse('menu-item-list')
        response = driver_client.post(url, menu_item_data, format='json')
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_restaurant_cannot_access_driver_functions(self, create_users, auth_client):
        """Test restaurant owners cannot access driver functions."""
        restaurant_owner = create_users['restaurant_owner']
        restaurant_client = auth_client(user=restaurant_owner)
        
        # Try to update driver location
        location_data = {
            'latitude': '40.7128',
            'longitude': '-74.0060'
        }
        
        url = reverse('driver-location-list')
        response = restaurant_client.post(url, location_data, format='json')
        
        assert response.status_code == status.HTTP_403_FORBIDDEN