from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from users.models import CustomUser, CustomerProfile, DriverProfile, RestaurantProfile
import uuid


class UserRegistrationTests(APITestCase):
    
    def test_register_customer(self):
        """
        Ensure we can register a new customer user.
        """
        url = reverse('users:register')
        data = {
            'email': 'customer@example.com',
            'full_name': 'Test Customer',
            'phone': '+1234567890',
            'password': 'strongpassword123',
            'password_confirm': 'strongpassword123',
            'role': 'CUSTOMER',
            'customer_profile': {
                'default_address': '123 Test St, Test City'
            }
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(CustomUser.objects.count(), 1)
        self.assertEqual(CustomerProfile.objects.count(), 1)
        
        user = CustomUser.objects.get(email='customer@example.com')
        self.assertEqual(user.full_name, 'Test Customer')
        self.assertEqual(user.role, 'CUSTOMER')
        
    def test_register_driver(self):
        """
        Ensure we can register a new driver user.
        """
        url = reverse('users:register')
        data = {
            'email': 'driver@example.com',
            'full_name': 'Test Driver',
            'phone': '+1234567891',
            'password': 'strongpassword123',
            'password_confirm': 'strongpassword123',
            'role': 'DRIVER',
            'driver_profile': {
                'vehicle_type': 'Car',
                'license_number': 'DL12345'
            }
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(CustomUser.objects.count(), 1)
        self.assertEqual(DriverProfile.objects.count(), 1)
        
        user = CustomUser.objects.get(email='driver@example.com')
        self.assertEqual(user.full_name, 'Test Driver')
        self.assertEqual(user.role, 'DRIVER')
        
    def test_register_restaurant(self):
        """
        Ensure we can register a new restaurant user.
        """
        url = reverse('users:register')
        data = {
            'email': 'restaurant@example.com',
            'full_name': 'Test Owner',
            'phone': '+1234567892',
            'password': 'strongpassword123',
            'password_confirm': 'strongpassword123',
            'role': 'RESTAURANT',
            'restaurant_profile': {
                'business_name': 'Test Restaurant',
                'business_address': '456 Restaurant St, Test City',
                'business_registration_number': 'BR12345'
            }
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(CustomUser.objects.count(), 1)
        self.assertEqual(RestaurantProfile.objects.count(), 1)
        
        user = CustomUser.objects.get(email='restaurant@example.com')
        self.assertEqual(user.full_name, 'Test Owner')
        self.assertEqual(user.role, 'RESTAURANT')
        
    def test_register_with_mismatched_passwords(self):
        """
        Ensure registration fails when passwords don't match.
        """
        url = reverse('users:register')
        data = {
            'email': 'test@example.com',
            'full_name': 'Test User',
            'password': 'password123',
            'password_confirm': 'password456',
            'role': 'CUSTOMER'
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(CustomUser.objects.count(), 0)


class UserAuthenticationTests(APITestCase):
    
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            email='test@example.com',
            full_name='Test User',
            password='testpassword',
            role='CUSTOMER'
        )
        CustomerProfile.objects.create(user=self.user)
        
    def test_login(self):
        """
        Ensure we can login with valid credentials.
        """
        url = reverse('users:token_obtain_pair')
        data = {
            'email': 'test@example.com',
            'password': 'testpassword'
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        
    def test_login_invalid_credentials(self):
        """
        Ensure login fails with invalid credentials.
        """
        url = reverse('users:token_obtain_pair')
        data = {
            'email': 'test@example.com',
            'password': 'wrongpassword'
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
    def test_token_refresh(self):
        """
        Ensure we can refresh the token.
        """
        # First, get the token
        login_url = reverse('users:token_obtain_pair')
        login_data = {
            'email': 'test@example.com',
            'password': 'testpassword'
        }
        
        login_response = self.client.post(login_url, login_data, format='json')
        refresh_token = login_response.data['refresh']
        
        # Then, refresh the token
        refresh_url = reverse('users:token_refresh')
        refresh_data = {
            'refresh': refresh_token
        }
        
        refresh_response = self.client.post(refresh_url, refresh_data, format='json')
        self.assertEqual(refresh_response.status_code, status.HTTP_200_OK)
        self.assertIn('access', refresh_response.data)


class UserProfileTests(APITestCase):
    
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            email='customer@example.com',
            full_name='Test Customer',
            password='testpassword',
            role='CUSTOMER'
        )
        self.customer_profile = CustomerProfile.objects.create(
            user=self.user,
            default_address='123 Test St, Test City'
        )
        
        self.driver = CustomUser.objects.create_user(
            email='driver@example.com',
            full_name='Test Driver',
            password='testpassword',
            role='DRIVER'
        )
        self.driver_profile = DriverProfile.objects.create(
            user=self.driver,
            vehicle_type='Car',
            license_number='DL12345'
        )
        
        # Login as the customer
        url = reverse('users:token_obtain_pair')
        data = {
            'email': 'customer@example.com',
            'password': 'testpassword'
        }
        
        response = self.client.post(url, data, format='json')
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['access']}")
        
    def test_get_own_profile(self):
        """
        Ensure users can retrieve their own profile.
        """
        url = reverse('users:profile')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], 'customer@example.com')
        self.assertEqual(response.data['customer_profile']['default_address'], '123 Test St, Test City')
        
    def test_update_profile(self):
        """
        Ensure users can update their profile.
        """
        url = reverse('users:profile')
        data = {
            'full_name': 'Updated Customer Name',
            'phone': '+9876543210',
            'customer_profile': {
                'default_address': '456 Updated St, New City',
                'default_location_lat': '40.7128',
                'default_location_lng': '-74.0060'
            }
        }
        
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Refresh from database
        self.user.refresh_from_db()
        self.customer_profile.refresh_from_db()
        
        self.assertEqual(self.user.full_name, 'Updated Customer Name')
        self.assertEqual(self.user.phone, '+9876543210')
        self.assertEqual(self.customer_profile.default_address, '456 Updated St, New City')
        
    def test_change_password(self):
        """
        Ensure users can change their password.
        """
        url = reverse('users:change_password')
        data = {
            'current_password': 'testpassword',
            'new_password': 'newpassword123',
            'new_password_confirm': 'newpassword123'
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify the password was changed by logging in with the new password
        self.client.credentials()  # Clear credentials
        login_url = reverse('users:token_obtain_pair')
        login_data = {
            'email': 'customer@example.com',
            'password': 'newpassword123'
        }
        
        login_response = self.client.post(login_url, login_data, format='json')
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)