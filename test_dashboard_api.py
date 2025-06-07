#!/usr/bin/env python
"""
Test script for dashboard APIs
"""
import os
import django
import sys

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'delivery.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from restaurants.models import Restaurant
from orders.models import Order
from decimal import Decimal
import json
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()

def get_jwt_token(user):
    """Get JWT token for a user"""
    refresh = RefreshToken.for_user(user)
    return str(refresh.access_token)

def test_dashboard_apis():
    """Test the dashboard APIs"""
    client = Client()
    
    # Create test users
    print("Creating test users...")
    
    # Create admin user (or get existing)
    admin_user, created = User.objects.get_or_create(
        email='admin@test.com',
        defaults={
            'password': 'testpass123',
            'full_name': 'Admin User',
            'role': 'ADMIN',
            'is_staff': True
        }
    )
    if created:
        admin_user.set_password('testpass123')
        admin_user.save()
    
    # Create restaurant user (or get existing)
    restaurant_user, created = User.objects.get_or_create(
        email='restaurant@test.com',
        defaults={
            'password': 'testpass123',
            'full_name': 'Restaurant Owner',
            'role': 'RESTAURANT'
        }
    )
    if created:
        restaurant_user.set_password('testpass123')
        restaurant_user.save()
    
    # Create restaurant (or get existing)
    restaurant, created = Restaurant.objects.get_or_create(
        user=restaurant_user,
        defaults={
            'name': 'Test Restaurant',
            'address': '123 Test St',
            'description': 'Test restaurant for API testing'
        }
    )
    
    # Create customer user (or get existing)
    customer_user, created = User.objects.get_or_create(
        email='customer@test.com',
        defaults={
            'password': 'testpass123',
            'full_name': 'Test Customer',
            'role': 'CUSTOMER'
        }
    )
    if created:
        customer_user.set_password('testpass123')
        customer_user.save()
    
    # Create test orders
    print("Creating test orders...")
    for i in range(5):
        Order.objects.create(
            customer=customer_user,
            restaurant=restaurant,
            status='DELIVERED' if i < 3 else 'PREPARING',
            delivery_address='123 Customer St',
            total_price=Decimal('25.00') + Decimal(str(i * 5)),
            delivery_fee=Decimal('3.00')
        )
    
    print("Testing APIs...")
    
    # Get JWT tokens for users
    admin_token = get_jwt_token(admin_user)
    restaurant_token = get_jwt_token(restaurant_user)
    
    # Test 1: Admin user accessing statistics
    print("\n1. Testing admin access to statistics...")
    response = client.get('/api/orders/dashboard/statistics/',
                         HTTP_AUTHORIZATION=f'Bearer {admin_token}')
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Statistics: {json.dumps(data, indent=2)}")
    else:
        print(f"Error: {response.content}")
    
    # Test 2: Restaurant owner accessing statistics
    print("\n2. Testing restaurant owner access to statistics...")
    response = client.get('/api/orders/dashboard/statistics/',
                         HTTP_AUTHORIZATION=f'Bearer {restaurant_token}')
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Statistics: {json.dumps(data, indent=2)}")
    else:
        print(f"Error: {response.content}")
    
    # Test 3: Recent orders
    print("\n3. Testing recent orders...")
    response = client.get('/api/orders/dashboard/recent-orders/',
                         HTTP_AUTHORIZATION=f'Bearer {restaurant_token}')
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Orders count: {data['count']}")
        print(f"First order: {json.dumps(data['results'][0] if data['results'] else 'No orders', indent=2)}")
    else:
        print(f"Error: {response.content}")
    
    # Test 4: Filter by status
    print("\n4. Testing filter by status...")
    response = client.get('/api/orders/dashboard/statistics/?status=DELIVERED',
                         HTTP_AUTHORIZATION=f'Bearer {restaurant_token}')
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Delivered orders statistics: {json.dumps(data, indent=2)}")
    else:
        print(f"Error: {response.content}")
    
    # Test 5: Admin accessing restaurants list
    print("\n5. Testing restaurants list (admin only)...")
    response = client.get('/api/orders/dashboard/restaurants/',
                         HTTP_AUTHORIZATION=f'Bearer {admin_token}')
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Restaurants: {json.dumps(data, indent=2)}")
    else:
        print(f"Error: {response.content}")
    
    # Test 6: Restaurant owner trying to access restaurants list (should fail)
    print("\n6. Testing restaurant owner access to restaurants list (should fail)...")
    response = client.get('/api/orders/dashboard/restaurants/',
                         HTTP_AUTHORIZATION=f'Bearer {restaurant_token}')
    print(f"Status: {response.status_code}")
    if response.status_code != 200:
        print(f"Expected error: {response.json()}")
    
    print("\n✅ Dashboard API tests completed!")

if __name__ == '__main__':
    test_dashboard_apis()