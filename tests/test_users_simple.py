import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from . import signal_helpers

@pytest.mark.django_db
class TestBasicUserFunctionality:
    """Simple tests that should pass regardless of implementation details."""
    
    @pytest.mark.parametrize("user_role", ["CUSTOMER", "DRIVER", "RESTAURANT"])
    def test_user_registration(self, api_client, user_role, disconnect_signals = signal_helpers.disconnect_signals):
        """Test user registration with different roles."""
        # Create test data
        test_email = f"{user_role.lower()}@example.com"
        test_data = {
            'email': test_email,
            'full_name': f'Test {user_role}',
            'password': 'testpassword123',
            'password_confirm': 'testpassword123',
            'role': user_role
        }
        
        # Add profile data if needed (implementation might require it)
        if user_role == 'CUSTOMER':
            test_data['customer_profile'] = {'default_address': '123 Test St'}
        elif user_role == 'DRIVER':
            test_data['driver_profile'] = {'vehicle_type': 'Car'}
        elif user_role == 'RESTAURANT':
            test_data['restaurant_profile'] = {
                'business_name': 'Test Restaurant',
                'business_address': '456 Restaurant St'
            }
        
        # Register user
        url = reverse('users:register')
        response = api_client.post(url, test_data, format='json')
        
        # Check status code (201 Created or 200 OK both acceptable)
        assert response.status_code in [status.HTTP_201_CREATED, status.HTTP_200_OK]
        
        # Verify user was created in database
        from users.models import CustomUser
        user = CustomUser.objects.filter(email=test_email).first()
        assert user is not None
        assert user.role == user_role
    
    def test_user_login(self, api_client, disconnect_signals):
        """Test basic user login with JWT."""
        # Create a test user first
        from users.models import CustomUser
        email = "logintest@example.com"
        password = "testpassword123"
        
        CustomUser.objects.create_user(
            email=email,
            password=password,
            full_name='Login Test User',
            role='CUSTOMER'
        )
        
        # Attempt login
        url = reverse('users:token_obtain_pair')
        data = {
            'email': email,
            'password': password
        }
        
        response = api_client.post(url, data, format='json')
        
        # Check response
        assert response.status_code == status.HTTP_200_OK
        assert 'access' in response.data
        assert 'refresh' in response.data
    
    def test_protected_endpoint(self, api_client, disconnect_signals):
        """Test accessing a protected endpoint with JWT."""
        # Create a test user first
        from users.models import CustomUser
        from rest_framework_simplejwt.tokens import RefreshToken
        
        email = "protectedtest@example.com"
        password = "testpassword123"
        
        user = CustomUser.objects.create_user(
            email=email,
            password=password,
            full_name='Protected Test User',
            role='CUSTOMER'
        )
        
        # Generate token manually
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        
        # Attempt to access protected endpoint without token
        url = reverse('users:profile')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        
        # Attempt to access with token
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK