#!/usr/bin/env python
"""
Mock Data Generator for Delivery Platform

This script populates the database with realistic mock data using the API endpoints.
It creates restaurant owners, restaurants, menu items, customers, drivers, orders, and deliveries.
"""

import requests
import json
import random
import time
import logging
from faker import Faker
from decimal import Decimal, ROUND_HALF_UP
import sys
from datetime import datetime, timedelta
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize Faker
fake = Faker()

# Configuration
API_BASE_URL = "http://localhost:8000/api"  # Update this with your API URL
ADMIN_EMAIL = "admin@example.com"
ADMIN_PASSWORD = "adminpassword"

# User counts
NUM_RESTAURANT_OWNERS = 3
NUM_CUSTOMERS = 10
NUM_DRIVERS = 5

# Restaurant configuration
MENU_CATEGORIES_PER_RESTAURANT = 3
MENU_ITEMS_PER_CATEGORY = [3, 5]  # Min and max menu items per category

# Order configuration
ORDERS_PER_CUSTOMER = [1, 3]  # Min and max orders per customer
ITEMS_PER_ORDER = [1, 4]  # Min and max items per order

# Food categories and sample items for each category
FOOD_CATEGORIES = {
    "Appetizers": [
        {"name": "Garlic Bread", "price": "4.99", "description": "Toasted bread with garlic butter and herbs"},
        {"name": "Mozzarella Sticks", "price": "6.99", "description": "Deep-fried mozzarella with marinara sauce"},
        {"name": "Buffalo Wings", "price": "8.99", "description": "Spicy chicken wings with blue cheese dip"},
        {"name": "Spinach Artichoke Dip", "price": "7.99", "description": "Creamy dip with spinach, artichokes, and cheese"},
        {"name": "Loaded Nachos", "price": "9.99", "description": "Tortilla chips with cheese, jalapeños, and sour cream"},
        {"name": "Calamari", "price": "10.99", "description": "Fried squid rings with aioli dip"},
        {"name": "Bruschetta", "price": "5.99", "description": "Toasted bread topped with tomatoes, basil, and olive oil"},
        {"name": "Spring Rolls", "price": "6.49", "description": "Vegetable filled rolls with sweet chili sauce"}
    ],
    "Main Courses": [
        {"name": "Margherita Pizza", "price": "12.99", "description": "Classic pizza with tomato, mozzarella, and basil"},
        {"name": "Cheeseburger", "price": "10.99", "description": "Beef patty with cheese, lettuce, and tomato"},
        {"name": "Grilled Salmon", "price": "16.99", "description": "Fresh salmon with lemon butter sauce"},
        {"name": "Spaghetti Carbonara", "price": "13.99", "description": "Pasta with creamy egg sauce and bacon"},
        {"name": "Caesar Salad", "price": "9.99", "description": "Romaine lettuce, croutons, and Caesar dressing"},
        {"name": "Chicken Tikka Masala", "price": "14.99", "description": "Spicy chicken curry with rice"},
        {"name": "Beef Stir Fry", "price": "15.99", "description": "Stir-fried beef and vegetables with rice"},
        {"name": "Vegetable Lasagna", "price": "13.49", "description": "Layers of pasta, vegetables, and cheese"},
        {"name": "Fish & Chips", "price": "11.99", "description": "Beer-battered fish with French fries"},
        {"name": "Steak & Fries", "price": "18.99", "description": "Grilled steak with garlic butter and fries"}
    ],
    "Desserts": [
        {"name": "Chocolate Cake", "price": "6.99", "description": "Rich chocolate cake with ganache"},
        {"name": "Cheesecake", "price": "7.99", "description": "Creamy New York style cheesecake"},
        {"name": "Tiramisu", "price": "6.49", "description": "Coffee-flavored Italian dessert"},
        {"name": "Apple Pie", "price": "5.99", "description": "Classic apple pie with cinnamon"},
        {"name": "Ice Cream Sundae", "price": "4.99", "description": "Vanilla ice cream with chocolate sauce and nuts"},
        {"name": "Crème Brûlée", "price": "7.49", "description": "Vanilla custard with caramelized sugar top"}
    ],
    "Drinks": [
        {"name": "Coke", "price": "2.49", "description": "Classic cola drink"},
        {"name": "Lemonade", "price": "2.99", "description": "Fresh-squeezed lemonade"},
        {"name": "Iced Tea", "price": "2.49", "description": "Sweet or unsweetened tea"},
        {"name": "Coffee", "price": "2.99", "description": "Freshly brewed coffee"},
        {"name": "Milkshake", "price": "4.99", "description": "Chocolate, vanilla, or strawberry"},
        {"name": "Smoothie", "price": "5.49", "description": "Fresh fruit smoothie"}
    ],
    "Sides": [
        {"name": "French Fries", "price": "3.99", "description": "Crispy fried potatoes"},
        {"name": "Onion Rings", "price": "4.49", "description": "Battered and fried onion rings"},
        {"name": "Coleslaw", "price": "2.99", "description": "Fresh cabbage salad"},
        {"name": "Mashed Potatoes", "price": "3.49", "description": "Creamy mashed potatoes with gravy"},
        {"name": "Side Salad", "price": "3.99", "description": "Mixed greens with balsamic dressing"}
    ]
}

# Restaurant types and names
RESTAURANT_TYPES = [
    {"type": "Italian", "categories": ["Appetizers", "Main Courses", "Desserts", "Drinks"]},
    {"type": "American", "categories": ["Appetizers", "Main Courses", "Desserts", "Drinks", "Sides"]},
    {"type": "Asian", "categories": ["Appetizers", "Main Courses", "Desserts", "Drinks"]},
    {"type": "Mexican", "categories": ["Appetizers", "Main Courses", "Desserts", "Drinks"]},
    {"type": "Indian", "categories": ["Appetizers", "Main Courses", "Desserts", "Drinks"]}
]

# User data
user_data = {
    "restaurant_owners": [],
    "customers": [],
    "drivers": [],
}

# Restaurant data
restaurant_data = []


def make_request(method, endpoint, data=None, token=None, files=None):
    """Make a request to the API with proper error handling."""
    url = f"{API_BASE_URL}/{endpoint}"
    headers = {}
    
    if token:
        headers['Authorization'] = f'Bearer {token}'
    
    try:
        if method.lower() == 'get':
            response = requests.get(url, headers=headers)
        elif method.lower() == 'post':
            response = requests.post(url, json=data, headers=headers, files=files)
        elif method.lower() == 'put':
            response = requests.put(url, json=data, headers=headers)
        elif method.lower() == 'patch':
            response = requests.patch(url, json=data, headers=headers)
        elif method.lower() == 'delete':
            response = requests.delete(url, headers=headers)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")
        
        # Check if the request was successful
        response.raise_for_status()
        
        # Return the JSON response if there is one
        if response.text:
            return response.json()
        return None
    
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP Error: {e}")
        logger.error(f"Response: {response.text}")
        return None
    except requests.exceptions.ConnectionError as e:
        logger.error(f"Connection Error: {e}")
        return None
    except requests.exceptions.Timeout as e:
        logger.error(f"Timeout Error: {e}")
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"Request Exception: {e}")
        return None


def get_auth_token(email, password):
    """Get authentication token for a user."""
    data = {"email": email, "password": password}
    response = make_request('post', 'users/token/', data)
    
    if response and 'access' in response:
        return response['access']
    else:
        logger.error(f"Failed to get token for {email}")
        return None


def register_user(role, index=0):
    """Register a new user with the given role."""
    first_name = fake.first_name()
    last_name = fake.last_name()
    full_name = f"{first_name} {last_name}"
    email = f"{role.lower()}{index}@example.com"
    password = "Pass1234!"
    
    user_data = {
        "email": email,
        "full_name": full_name,
        "phone": fake.phone_number(),
        "password": password,
        "password_confirm": password,
        "role": role.upper()
    }
    
    # Add role-specific profile data
    if role.upper() == 'CUSTOMER':
        user_data["customer_profile"] = {
            "default_address": fake.address(),
            "default_location_lat": float(fake.latitude()),
            "default_location_lng": float(fake.longitude())
        }
    elif role.upper() == 'DRIVER':
        user_data["driver_profile"] = {
            "vehicle_type": random.choice(["Car", "Motorcycle", "Bicycle", "Scooter"]),
            "license_number": fake.bothify("DL-####-????").upper()
        }
    elif role.upper() == 'RESTAURANT':
        business_name = f"{fake.last_name()}'s {random.choice(RESTAURANT_TYPES)['type']} Restaurant"
        user_data["restaurant_profile"] = {
            "business_name": business_name,
            "business_address": fake.address(),
            "business_registration_number": fake.bothify("BR-####-????").upper()
        }
    
    response = make_request('post', 'users/register/', user_data)
    
    if response:
        logger.info(f"Registered {role} user: {email}")
        # Get auth token
        token = get_auth_token(email, password)
        
        return {
            "email": email,
            "full_name": full_name,
            "password": password,
            "token": token,
            "id": response.get('id'),
            "data": response
        }
    else:
        logger.error(f"Failed to register {role} user")
        return None


def create_restaurant(owner):
    """Create a restaurant for a restaurant owner."""
    restaurant_type = random.choice(RESTAURANT_TYPES)
    business_name = f"{owner['full_name'].split()[0]}'s {restaurant_type['type']} Restaurant"
    
    restaurant_data = {
        "name": business_name,
        "address": fake.address(),
        "description": fake.paragraph(),
        "location_lat": str(float(fake.latitude())),
        "location_lng": str(float(fake.longitude())),
        "is_open": True,
        "opening_time": "08:00:00",
        "closing_time": "22:00:00"
    }
    
    response = make_request('post', 'restaurants/restaurants/', restaurant_data, owner['token'])
    
    if response:
        logger.info(f"Created restaurant: {business_name}")
        return {
            "id": response['id'],
            "name": business_name,
            "type": restaurant_type,
            "data": response
        }
    else:
        logger.error(f"Failed to create restaurant for {owner['email']}")
        return None


def create_menu_categories(restaurant, owner):
    """Create menu categories for a restaurant."""
    categories = []
    restaurant_type = restaurant['type']
    
    # Select a subset of categories for the restaurant
    selected_categories = random.sample(
        restaurant_type['categories'], 
        min(MENU_CATEGORIES_PER_RESTAURANT, len(restaurant_type['categories']))
    )
    
    for i, category_name in enumerate(selected_categories):
        category_data = {
            "restaurant": restaurant['id'],
            "name": category_name,
            "description": fake.sentence(),
            "order": i + 1
        }
        
        response = make_request('post', 'restaurants/categories/', category_data, owner['token'])
        
        if response:
            logger.info(f"Created menu category: {category_name} for {restaurant['name']}")
            categories.append({
                "id": response['id'],
                "name": category_name,
                "data": response
            })
        else:
            logger.error(f"Failed to create menu category for {restaurant['name']}")
    
    return categories


def create_menu_items(restaurant, categories, owner):
    """Create menu items for each category in the restaurant."""
    items = []
    
    for category in categories:
        # Get the appropriate food items for this category
        if category['name'] in FOOD_CATEGORIES:
            food_items = FOOD_CATEGORIES[category['name']]
            
            # Determine how many items to create
            num_items = random.randint(MENU_ITEMS_PER_CATEGORY[0], min(MENU_ITEMS_PER_CATEGORY[1], len(food_items)))
            
            # Select random items from the food_items list
            selected_items = random.sample(food_items, num_items)
            
            for item in selected_items:
                item_data = {
                    "restaurant": restaurant['id'],
                    "category": category['id'],
                    "name": item['name'],
                    "description": item['description'],
                    "price": item['price'],
                    "is_available": True,
                    "is_featured": random.choice([True, False]),
                    "preparation_time": random.randint(5, 30)
                }
                
                response = make_request('post', 'restaurants/menu-items/', item_data, owner['token'])
                
                if response:
                    logger.info(f"Created menu item: {item['name']} for {restaurant['name']}")
                    items.append({
                        "id": response['id'],
                        "name": item['name'],
                        "price": item['price'],
                        "data": response
                    })
                else:
                    logger.error(f"Failed to create menu item for {restaurant['name']}")
    
    return items


def create_order(customer, restaurant, menu_items):
    """Create an order for a customer."""
    # Select random menu items for the order
    num_items = random.randint(ITEMS_PER_ORDER[0], ITEMS_PER_ORDER[1])
    selected_items = random.sample(menu_items, min(num_items, len(menu_items)))
    
    order_items = []
    for item in selected_items:
        quantity = random.randint(1, 3)
        order_items.append({
            "menu_item": item['id'],
            "quantity": quantity,
            "notes": fake.sentence() if random.choice([True, False]) else ""
        })
    
    order_data = {
        "restaurant": restaurant['id'],
        "delivery_address": fake.address(),
        "delivery_lat": str(float(fake.latitude())),
        "delivery_lng": str(float(fake.longitude())),
        "delivery_fee": "2.50",
        "notes": fake.paragraph() if random.choice([True, False]) else "",
        "items": order_items
    }
    
    response = make_request('post', 'orders/', order_data, customer['token'])
    
    if response:
        logger.info(f"Created order for {customer['full_name']} at {restaurant['name']}")
        return {
            "id": response['id'],
            "customer": customer['full_name'],
            "restaurant": restaurant['name'],
            "data": response
        }
    else:
        logger.error(f"Failed to create order for {customer['full_name']}")
        return None


def process_order(order, restaurant_owner, driver=None):
    """Process an order through the restaurant and driver workflows."""
    # Restaurant accepts order
    response = make_request(
        'post', 
        f"orders/{order['id']}/restaurant_action/", 
        {"action": "accept", "note": "Order accepted"}, 
        restaurant_owner['token']
    )
    
    if not response:
        logger.error(f"Failed to accept order {order['id']}")
        return False
    
    logger.info(f"Restaurant accepted order {order['id']}")
    
    # Restaurant prepares order
    response = make_request(
        'post', 
        f"orders/{order['id']}/preparing/", 
        {"note": "Order is being prepared"}, 
        restaurant_owner['token']
    )
    
    if not response:
        logger.error(f"Failed to prepare order {order['id']}")
        return False
    
    logger.info(f"Restaurant preparing order {order['id']}")
    
    # Update order status to ready for pickup
    response = make_request(
        'patch', 
        f"orders/{order['id']}/", 
        {
            "status": "READY_FOR_PICKUP",
            "status_note": "Order is ready for pickup"
        }, 
        restaurant_owner['token']
    )
    
    if not response:
        logger.error(f"Failed to mark order {order['id']} as ready for pickup")
        return False
    
    logger.info(f"Order {order['id']} ready for pickup")
    
    # If a driver is provided, assign and complete the delivery
    if driver and driver['token']:
        # Admin assigns task to driver
        admin_token = get_auth_token(ADMIN_EMAIL, ADMIN_PASSWORD)
        
        if not admin_token:
            logger.error(f"Failed to get admin token")
            return False
        
        # Create driver task for the order
        # In this updated version, we'll manually construct a task
        # since the API endpoint might be different
        driver_id = None
        try:
            if 'driver_profile' in driver['data']:
                driver_id = driver['data']['driver_profile']['id']
            elif 'id' in driver['data']:
                driver_id = driver['data']['id']
        except (KeyError, TypeError):
            logger.error(f"Couldn't determine driver ID")
            return False
        
        if not driver_id:
            logger.error(f"Missing driver ID")
            return False
            
        # Assign task to driver
        task_data = {
            "driver": driver_id,
            "order": order['id'],
            "status": "PENDING",
            "notes": "Please pick up from the restaurant."
        }
        
        # Using the appropriate endpoint for creating driver tasks
        task_response = make_request('post', 'drivers/tasks/', task_data, admin_token)
        
        if not task_response:
            logger.error(f"Failed to assign task for order {order['id']} to driver {driver['full_name']}")
            return False
        
        task_id = task_response.get('id')
        if not task_id:
            logger.error(f"No task ID returned after task creation")
            return False
            
        logger.info(f"Task assigned to driver {driver['full_name']} for order {order['id']}")
        
        # Driver accepts task
        accept_response = make_request('post', f"drivers/tasks/{task_id}/accept/", {}, driver['token'])
        
        if not accept_response:
            logger.error(f"Failed to accept task {task_id}")
            return False
        
        logger.info(f"Driver {driver['full_name']} accepted task {task_id}")
        
        # Driver picks up order
        pickup_response = make_request('post', f"drivers/tasks/{task_id}/picked_up/", {}, driver['token'])
        
        if not pickup_response:
            logger.error(f"Failed to mark task {task_id} as picked up")
            return False
        
        logger.info(f"Driver {driver['full_name']} picked up order {order['id']}")
        
        # Driver delivers order
        deliver_response = make_request('post', f"drivers/tasks/{task_id}/delivered/", {}, driver['token'])
        
        if not deliver_response:
            logger.error(f"Failed to mark task {task_id} as delivered")
            return False
        
        logger.info(f"Driver {driver['full_name']} delivered order {order['id']}")
    
    return True


def update_driver_location(driver):
    """Update the driver's location."""
    location_data = {
        "latitude": str(float(fake.latitude())),
        "longitude": str(float(fake.longitude())),
        "accuracy": round(random.uniform(1, 10), 2)
    }
    
    # Check if driver profile ID is available
    if 'data' in driver and 'driver_profile' in driver['data']:
        driver_profile_id = driver['data']['driver_profile']['id'] 
        location_data['driver'] = driver_profile_id
    
    response = make_request('post', 'drivers/locations/', location_data, driver['token'])
    
    if response:
        logger.info(f"Updated location for driver {driver['full_name']}")
        return True
    else:
        logger.error(f"Failed to update location for driver {driver['full_name']}")
        return False


def update_driver_availability(driver, status):
    """Update the driver's availability status."""
    if status.upper() == 'AVAILABLE':
        endpoint = 'drivers/availability/go_online/'
    else:
        endpoint = 'drivers/availability/go_offline/'
    
    response = make_request('post', endpoint, {}, driver['token'])
    
    if response:
        logger.info(f"Updated availability for driver {driver['full_name']} to {status}")
        return True
    else:
        logger.error(f"Failed to update availability for driver {driver['full_name']}")
        return False


def create_restaurant_review(customer, restaurant):
    """Create a review for a restaurant."""
    review_data = {
        "restaurant": restaurant['id'],
        "rating": random.randint(3, 5),  # Mostly positive reviews 3-5 stars
        "comment": fake.paragraph()
    }
    
    response = make_request('post', 'restaurants/reviews/', review_data, customer['token'])
    
    if response:
        logger.info(f"Created review for {restaurant['name']} by {customer['full_name']}")
        return True
    else:
        logger.error(f"Failed to create review for {restaurant['name']}")
        return False


def main():
    """Main function to populate the database with mock data."""
    start_time = time.time()
    logger.info("Starting mock data generation")
    
    # Register restaurant owners
    logger.info(f"Registering {NUM_RESTAURANT_OWNERS} restaurant owners...")
    for i in range(NUM_RESTAURANT_OWNERS):
        owner = register_user('RESTAURANT', i + 1)
        if owner:
            user_data['restaurant_owners'].append(owner)
    
    # Create restaurants
    logger.info("Creating restaurants...")
    for owner in user_data['restaurant_owners']:
        restaurant = create_restaurant(owner)
        if restaurant:
            # Create menu categories for the restaurant
            categories = create_menu_categories(restaurant, owner)
            
            # Create menu items for each category
            menu_items = create_menu_items(restaurant, categories, owner)
            
            # Add complete restaurant data
            restaurant_data.append({
                "restaurant": restaurant,
                "owner": owner,
                "categories": categories,
                "menu_items": menu_items
            })
    
    # Register customers
    logger.info(f"Registering {NUM_CUSTOMERS} customers...")
    for i in range(NUM_CUSTOMERS):
        customer = register_user('CUSTOMER', i + 1)
        if customer:
            user_data['customers'].append(customer)
    
    # Register drivers
    logger.info(f"Registering {NUM_DRIVERS} drivers...")
    for i in range(NUM_DRIVERS):
        driver = register_user('DRIVER', i + 1)
        if driver:
            user_data['drivers'].append(driver)
            
            # Update driver location and availability
            update_driver_location(driver)
            update_driver_availability(driver, 'AVAILABLE')
    
    # Create orders for each customer
    logger.info("Creating and processing orders...")
    all_orders = []
    
    for customer in user_data['customers']:
        # Determine number of orders for this customer
        num_orders = random.randint(ORDERS_PER_CUSTOMER[0], ORDERS_PER_CUSTOMER[1])
        
        for _ in range(num_orders):
            # Select random restaurant
            restaurant_info = random.choice(restaurant_data)
            restaurant = restaurant_info['restaurant']
            restaurant_owner = restaurant_info['owner']
            menu_items = restaurant_info['menu_items']
            
            # Create order
            order = create_order(customer, restaurant, menu_items)
            
            if order:
                all_orders.append(order)
                
                # Randomly assign a driver (or None for some orders)
                driver = random.choice(user_data['drivers']) if random.random() > 0.2 else None
                
                # Process the order
                process_order(order, restaurant_owner, driver)
                
    # Create reviews for restaurants
    logger.info("Creating restaurant reviews...")
    for customer in user_data['customers']:
        # Each customer reviews 1-2 random restaurants
        num_reviews = random.randint(1, min(2, len(restaurant_data)))
        reviewed_restaurants = random.sample(restaurant_data, num_reviews)
        
        for restaurant_info in reviewed_restaurants:
            create_restaurant_review(customer, restaurant_info['restaurant'])
    
    # Print summary
    end_time = time.time()
    run_time = end_time - start_time
    
    logger.info("=" * 50)
    logger.info("Mock data generation completed!")
    logger.info(f"Created {len(user_data['restaurant_owners'])} restaurant owners")
    logger.info(f"Created {len(restaurant_data)} restaurants")
    total_menu_items = sum(len(r['menu_items']) for r in restaurant_data)
    logger.info(f"Created {total_menu_items} menu items")
    logger.info(f"Created {len(user_data['customers'])} customers")
    logger.info(f"Created {len(user_data['drivers'])} drivers")
    logger.info(f"Created {len(all_orders)} orders")
    logger.info(f"Total runtime: {run_time:.2f} seconds")
    logger.info("=" * 50)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Script interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        sys.exit(1)