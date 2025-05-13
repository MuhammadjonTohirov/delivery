import pytest
from django.urls import reverse
from rest_framework import status
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

from users.models import CustomUser
from restaurants.models import Restaurant, MenuItem
from orders.models import Order

# Edge cases and failure scenarios for robustness testing

@pytest.mark.django_db
class TestOrderEdgeCases:
    
    def test_order_with_inactive_menu_item(self, create_users, setup_restaurant, auth_client):
        """Test ordering an item that has been marked as unavailable."""
        customer = create_users['customer']
        restaurant_owner = create_users['restaurant_owner']
        customer_client = auth_client(user=customer)
        restaurant_client = auth_client(user=restaurant_owner)
        
        restaurant = setup_restaurant['restaurant']
        menu_item = setup_restaurant['menu_items'][0]
        
        # First, restaurant owner marks item as unavailable
        url = reverse('menu-item-detail', args=[menu_item.id])
        response = restaurant_client.patch(url, {'is_available': False}, format='json')
        assert response.status_code == status.HTTP_200_OK
        
        # Customer tries to order the unavailable item
        order_data = {
            'restaurant': str(restaurant.id),
            'delivery_address': '123 Test St, Test City',
            'delivery_fee': '2.50',
            'items': [
                {
                    'menu_item': str(menu_item.id),
                    'quantity': 1
                }
            ]
        }
        
        url = reverse('order-list')
        response = customer_client.post(url, order_data, format='json')
        
        # Should fail with 400 Bad Request
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'unavailable' in str(response.data).lower()
    
    def test_order_with_closed_restaurant(self, create_users, setup_restaurant, auth_client):
        """Test ordering from a restaurant that is closed."""
        customer = create_users['customer']
        restaurant_owner = create_users['restaurant_owner']
        customer_client = auth_client(user=customer)
        restaurant_client = auth_client(user=restaurant_owner)
        
        restaurant = setup_restaurant['restaurant']
        menu_item = setup_restaurant['menu_items'][0]
        
        # First, restaurant owner marks restaurant as closed
        url = reverse('restaurant-detail', args=[restaurant.id])
        response = restaurant_client.patch(url, {'is_open': False}, format='json')
        assert response.status_code == status.HTTP_200_OK
        
        # Customer tries to order from the closed restaurant
        order_data = {
            'restaurant': str(restaurant.id),
            'delivery_address': '123 Test St, Test City',
            'delivery_fee': '2.50',
            'items': [
                {
                    'menu_item': str(menu_item.id),
                    'quantity': 1
                }
            ]
        }
        
        url = reverse('order-list')
        response = customer_client.post(url, order_data, format='json')
        
        # Should fail with 400 Bad Request
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'closed' in str(response.data).lower()
    
    def test_order_status_skipping_validation(self, create_users, setup_restaurant, auth_client):
        """Test that order status cannot skip steps in the workflow."""
        customer = create_users['customer']
        restaurant_owner = create_users['restaurant_owner']
        customer_client = auth_client(user=customer)
        restaurant_client = auth_client(user=restaurant_owner)
        
        restaurant = setup_restaurant['restaurant']
        menu_item = setup_restaurant['menu_items'][0]
        
        # Create an order
        order_data = {
            'restaurant': str(restaurant.id),
            'delivery_address': '123 Test St, Test City',
            'delivery_fee': '2.50',
            'items': [
                {
                    'menu_item': str(menu_item.id),
                    'quantity': 1
                }
            ]
        }
        
        url = reverse('order-list')
        response = customer_client.post(url, order_data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        order_id = response.data['id']
        
        # Try to mark order as ready for pickup without confirming or preparing first
        url = reverse('order-ready-for-pickup', args=[order_id])
        response = restaurant_client.post(url, format='json')
        
        # Should fail with 400 Bad Request
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'status' in str(response.data).lower()


@pytest.mark.django_db
class TestDriverEdgeCases:
    
    def test_driver_task_assignment_when_unavailable(self, create_users, setup_restaurant, setup_driver, auth_client):
        """Test assigning a task to a driver who is offline."""
        customer = create_users['customer']
        admin = create_users['admin']
        driver = create_users['driver']
        
        customer_client = auth_client(user=customer)
        admin_client = auth_client(user=admin)
        driver_client = auth_client(user=driver)
        
        restaurant = setup_restaurant['restaurant']
        menu_item = setup_restaurant['menu_items'][0]
        
        # First, set driver as offline
        url = reverse('driver-availability-go-offline')
        response = driver_client.post(url, format='json')
        assert response.status_code == status.HTTP_200_OK
        
        # Create an order
        order_data = {
            'restaurant': str(restaurant.id),
            'delivery_address': '123 Test St, Test City',
            'delivery_fee': '2.50',
            'items': [
                {
                    'menu_item': str(menu_item.id),
                    'quantity': 1
                }
            ]
        }
        
        url = reverse('order-list')
        response = customer_client.post(url, order_data, format='json')
        order_id = response.data['id']
        
        # Try to assign task to offline driver
        driver_task_data = {
            'driver': str(driver.driver_profile.id),
            'order': order_id,
            'status': 'PENDING'
        }
        
        url = reverse('driver-task-list')
        response = admin_client.post(url, driver_task_data, format='json')
        
        # Should fail with 400 Bad Request
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'offline' in str(response.data).lower() or 'unavailable' in str(response.data).lower()
    
    def test_driver_multiple_simultaneous_tasks(self, create_users, setup_restaurant, setup_driver, auth_client):
        """Test assigning multiple simultaneous tasks to a driver."""
        customer = create_users['customer']
        admin = create_users['admin']
        driver = create_users['driver']
        
        customer_client = auth_client(user=customer)
        admin_client = auth_client(user=admin)
        
        restaurant = setup_restaurant['restaurant']
        menu_item = setup_restaurant['menu_items'][0]
        
        # Create first order
        order_data = {
            'restaurant': str(restaurant.id),
            'delivery_address': '123 Test St, Test City',
            'delivery_fee': '2.50',
            'items': [
                {
                    'menu_item': str(menu_item.id),
                    'quantity': 1
                }
            ]
        }
        
        url = reverse('order-list')
        response = customer_client.post(url, order_data, format='json')
        order1_id = response.data['id']
        
        # Create second order
        response = customer_client.post(url, order_data, format='json')
        order2_id = response.data['id']
        
        # Assign first task to driver
        driver_task_data = {
            'driver': str(driver.driver_profile.id),
            'order': order1_id,
            'status': 'PENDING'
        }
        
        url = reverse('driver-task-list')
        response = admin_client.post(url, driver_task_data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        
        # Try to assign second task while first is pending
        driver_task_data = {
            'driver': str(driver.driver_profile.id),
            'order': order2_id,
            'status': 'PENDING'
        }
        
        response = admin_client.post(url, driver_task_data, format='json')
        
        # Should fail with 400 Bad Request due to driver busy with another task
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'busy' in str(response.data).lower() or 'active task' in str(response.data).lower()


@pytest.mark.django_db
class TestTimeoutAndCancellationScenarios:
    
    def test_order_auto_cancellation_on_timeout(self, create_users, setup_restaurant, auth_client, monkeypatch):
        """Test that orders are automatically cancelled if not accepted within a time window."""
        customer = create_users['customer']
        customer_client = auth_client(user=customer)
        
        restaurant = setup_restaurant['restaurant']
        menu_item = setup_restaurant['menu_items'][0]
        
        # Create an order
        order_data = {
            'restaurant': str(restaurant.id),
            'delivery_address': '123 Test St, Test City',
            'delivery_fee': '2.50',
            'items': [
                {
                    'menu_item': str(menu_item.id),
                    'quantity': 1
                }
            ]
        }
        
        url = reverse('order-list')
        response = customer_client.post(url, order_data, format='json')
        order_id = response.data['id']
        
        # Simulate order being created 30 minutes ago
        order = Order.objects.get(id=order_id)
        order.created_at = timezone.now() - timedelta(minutes=30)
        order.save()
        
        # Call the automatic cancellation function (would normally be triggered by Celery or cron)
        from orders.utils import cancel_timed_out_orders
        cancel_timed_out_orders()
        
        # Check if order was cancelled
        url = reverse('order-detail', args=[order_id])
        response = customer_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == 'CANCELLED'
    
    def test_customer_cancellation_before_preparation(self, create_users, setup_restaurant, auth_client):
        """Test that customers can cancel orders before preparation starts."""
        customer = create_users['customer']
        restaurant_owner = create_users['restaurant_owner']
        
        customer_client = auth_client(user=customer)
        restaurant_client = auth_client(user=restaurant_owner)
        
        restaurant = setup_restaurant['restaurant']
        menu_item = setup_restaurant['menu_items'][0]
        
        # Create an order
        order_data = {
            'restaurant': str(restaurant.id),
            'delivery_address': '123 Test St, Test City',
            'delivery_fee': '2.50',
            'items': [
                {
                    'menu_item': str(menu_item.id),
                    'quantity': 1
                }
            ]
        }
        
        url = reverse('order-list')
        response = customer_client.post(url, order_data, format='json')
        order_id = response.data['id']
        
        # Restaurant accepts the order
        url = reverse('order-restaurant-action', args=[order_id])
        response = restaurant_client.post(url, {'action': 'accept'}, format='json')
        assert response.status_code == status.HTTP_200_OK
        
        # Customer tries to cancel the order
        url = reverse('order-cancel', args=[order_id])
        response = customer_client.post(url, {'reason': 'Changed my mind.'}, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == 'CANCELLED'
        
        # Restaurant tries to mark the cancelled order as preparing
        url = reverse('order-preparing', args=[order_id])
        response = restaurant_client.post(url, format='json')
        
        # Should fail with 400 Bad Request
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'cancelled' in str(response.data).lower()
    
    def test_customer_cancellation_after_preparation(self, create_users, setup_restaurant, auth_client):
        """Test that customers cannot cancel orders after preparation starts."""
        customer = create_users['customer']
        restaurant_owner = create_users['restaurant_owner']
        
        customer_client = auth_client(user=customer)
        restaurant_client = auth_client(user=restaurant_owner)
        
        restaurant = setup_restaurant['restaurant']
        menu_item = setup_restaurant['menu_items'][0]
        
        # Create an order
        order_data = {
            'restaurant': str(restaurant.id),
            'delivery_address': '123 Test St, Test City',
            'delivery_fee': '2.50',
            'items': [
                {
                    'menu_item': str(menu_item.id),
                    'quantity': 1
                }
            ]
        }
        
        url = reverse('order-list')
        response = customer_client.post(url, order_data, format='json')
        order_id = response.data['id']
        
        # Restaurant accepts the order
        url = reverse('order-restaurant-action', args=[order_id])
        restaurant_client.post(url, {'action': 'accept'}, format='json')
        
        # Restaurant marks the order as preparing
        url = reverse('order-preparing', args=[order_id])
        restaurant_client.post(url, format='json')
        
        # Customer tries to cancel the order after preparation has started
        url = reverse('order-cancel', args=[order_id])
        response = customer_client.post(url, {'reason': 'Changed my mind.'}, format='json')
        
        # Should fail with 400 Bad Request
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'preparation' in str(response.data).lower()


@pytest.mark.django_db
class TestConcurrencyAndLoadScenarios:
    
    def test_menu_item_price_changes_after_order_placed(self, create_users, setup_restaurant, auth_client):
        """Test that orders use the price at the time of ordering."""
        customer = create_users['customer']
        restaurant_owner = create_users['restaurant_owner']
        
        customer_client = auth_client(user=customer)
        restaurant_client = auth_client(user=restaurant_owner)
        
        restaurant = setup_restaurant['restaurant']
        menu_item = setup_restaurant['menu_items'][0]
        original_price = menu_item.price
        
        # Create an order
        order_data = {
            'restaurant': str(restaurant.id),
            'delivery_address': '123 Test St, Test City',
            'delivery_fee': '2.50',
            'items': [
                {
                    'menu_item': str(menu_item.id),
                    'quantity': 1
                }
            ]
        }
        
        url = reverse('order-list')
        response = customer_client.post(url, order_data, format='json')
        order_id = response.data['id']
        item_subtotal = response.data['items'][0]['subtotal']
        
        # Restaurant owner changes the price of the menu item
        new_price = original_price + Decimal('5.00')
        url = reverse('menu-item-detail', args=[menu_item.id])
        response = restaurant_client.patch(url, {'price': str(new_price)}, format='json')
        assert response.status_code == status.HTTP_200_OK
        
        # Check the order still has the original price
        url = reverse('order-detail', args=[order_id])
        response = customer_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert Decimal(response.data['items'][0]['subtotal']) == item_subtotal
        assert Decimal(response.data['items'][0]['unit_price']) == original_price
    
    def test_high_volume_order_creation(self, create_users, setup_restaurant, auth_client):
        """Test the system can handle multiple simultaneous orders."""
        customer = create_users['customer']
        customer_client = auth_client(user=customer)
        
        restaurant = setup_restaurant['restaurant']
        menu_item = setup_restaurant['menu_items'][0]
        
        # Create base order data
        order_data = {
            'restaurant': str(restaurant.id),
            'delivery_address': '123 Test St, Test City',
            'delivery_fee': '2.50',
            'items': [
                {
                    'menu_item': str(menu_item.id),
                    'quantity': 1
                }
            ]
        }
        
        # Place 10 orders in rapid succession
        order_ids = []
        url = reverse('order-list')
        
        for i in range(10):
            # Slightly modify order to avoid exact duplicates
            order_data['notes'] = f'Order #{i+1}'
            response = customer_client.post(url, order_data, format='json')
            assert response.status_code == status.HTTP_201_CREATED
            order_ids.append(response.data['id'])
        
        # Verify all orders were created successfully
        assert len(order_ids) == 10
        
        # Verify all orders can be retrieved
        for order_id in order_ids:
            url = reverse('order-detail', args=[order_id])
            response = customer_client.get(url)
            assert response.status_code == status.HTTP_200_OK