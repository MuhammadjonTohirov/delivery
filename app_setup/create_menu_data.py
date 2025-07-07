from restaurants.models import MenuCategory, MenuItem, Restaurant
from django.core.files import File
import os

# Create menu categories if none exist
if MenuCategory.objects.count() == 0:
    categories_data = [
        {'name': 'Appetizers', 'description': 'Starters and small plates', 'order': 1, 'image_name': 'appetizers.png'},
        {'name': 'Soups & Salads', 'description': 'Fresh soups and salads', 'order': 2, 'image_name': 'soups_salads.png'},
        {'name': 'Main Courses', 'description': 'Main dishes and entrees', 'order': 3, 'image_name': 'main_courses.png'},
        {'name': 'Beverages', 'description': 'Hot and cold drinks', 'order': 4, 'image_name': 'beverages.png'},
        {'name': 'Pizza & Pasta', 'description': 'Italian classics', 'order': 5, 'image_name': 'pizza_pasta.png'},
        {'name': 'Desserts', 'description': 'Sweet treats and desserts', 'order': 6, 'image_name': 'dessets.png'},
    ]
    for cat_data in categories_data:
        image_name = cat_data.pop('image_name', None)
        category = MenuCategory.objects.create(**cat_data)
        
        # Set category image if available
        if image_name:
            # Search for image in multiple locations
            search_paths = [
                os.path.join('resources/category_images', image_name),
                os.path.join('resources/menu_images', image_name),
                os.path.join('resources/other_images', image_name),
                os.path.join('resources', image_name),
            ]
            
            # Also search in subdirectories
            for root_dir in ['resources/category_images', 'resources/menu_images', 'resources/other_images', 'resources']:
                if os.path.exists(root_dir):
                    for subdir in os.listdir(root_dir):
                        subdir_path = os.path.join(root_dir, subdir)
                        if os.path.isdir(subdir_path):
                            search_paths.append(os.path.join(subdir_path, image_name))
            
            image_found = False
            for image_path in search_paths:
                if os.path.exists(image_path):
                    try:
                        with open(image_path, 'rb') as f:
                            category.image.save(image_name, File(f))
                        print(f'Set image for category: {category.name} from {image_path}')
                        image_found = True
                        break
                    except Exception as e:
                        print(f'Error setting image for {category.name}: {e}')
            
            if not image_found:
                print(f'Image not found for {category.name}: {image_name} (searched in multiple locations)')
    
    print('Created 6 menu categories.')
else:
    print('Menu categories already exist.')

# Create menu items if none exist
if MenuItem.objects.count() == 0:
    restaurant = Restaurant.objects.first()
    if restaurant:
        menu_items_data = [
            # Appetizers
            {'name': 'Bruschetta', 'description': 'Grilled bread with tomatoes, garlic, and olive oil', 'price': 35000, 'category': 'Appetizers', 'image_name': 'beef_burger.png'},
            {'name': 'Garlic Bread', 'description': 'Buttery garlic bread', 'price': 28000, 'category': 'Appetizers', 'image_name': 'chicken_burger.png'},
            {'name': 'Mozzarella Sticks', 'description': 'Crispy fried mozzarella with marinara sauce', 'price': 42000, 'category': 'Appetizers', 'image_name': 'mexian_tacos.png'},
            
            # Soups & Salads
            {'name': 'Caesar Salad', 'description': 'Romaine lettuce with Caesar dressing', 'price': 45000, 'category': 'Soups & Salads', 'image_name': 'garden_salad.png'},
            {'name': 'Minestrone Soup', 'description': 'Thick soup of Italian origin', 'price': 40000, 'category': 'Soups & Salads', 'image_name': 'garden_salad.png'},
            {'name': 'Greek Salad', 'description': 'Fresh vegetables with feta cheese and olives', 'price': 48000, 'category': 'Soups & Salads', 'image_name': 'garden_salad.png'},
            
            # Main Courses
            {'name': 'Grilled Chicken', 'description': 'Herb-seasoned grilled chicken breast', 'price': 75000, 'category': 'Main Courses', 'image_name': 'chicken_burger.png'},
            {'name': 'Beef Steak', 'description': 'Premium beef steak with vegetables', 'price': 95000, 'category': 'Main Courses', 'image_name': 'beef_burger.png'},
            {'name': 'Fish & Chips', 'description': 'Crispy battered fish with french fries', 'price': 68000, 'category': 'Main Courses', 'image_name': 'fish_tacos.png'},
            
            # Beverages
            {'name': 'Fresh Orange Juice', 'description': 'Freshly squeezed orange juice', 'price': 25000, 'category': 'Beverages', 'image_name': 'chicken_burger.png'},
            {'name': 'Cappuccino', 'description': 'Italian coffee with steamed milk foam', 'price': 18000, 'category': 'Beverages', 'image_name': 'beef_burger.png'},
            {'name': 'Coca Cola', 'description': 'Classic soft drink', 'price': 12000, 'category': 'Beverages', 'image_name': 'garden_salad.png'},
            
            # Pizza & Pasta
            {'name': 'Margherita Pizza', 'description': 'Classic pizza with tomato, mozzarella, and basil', 'price': 55000, 'category': 'Pizza & Pasta', 'image_name': 'margaritta.png'},
            {'name': 'Spaghetti Carbonara', 'description': 'Pasta with eggs, cheese, and bacon', 'price': 65000, 'category': 'Pizza & Pasta', 'image_name': 'creamy_totata_pasta.png'},
            {'name': 'Pepperoni Pizza', 'description': 'Pizza topped with spicy pepperoni', 'price': 62000, 'category': 'Pizza & Pasta', 'image_name': 'margaritta.png'},
            
            # Desserts
            {'name': 'Tiramisu', 'description': 'Coffee-flavoured Italian dessert', 'price': 32000, 'category': 'Desserts', 'image_name': 'beef_burger.png'},
            {'name': 'Panna Cotta', 'description': 'Italian dessert of sweetened cream', 'price': 36000, 'category': 'Desserts', 'image_name': 'chicken_burger.png'},
            {'name': 'Chocolate Cake', 'description': 'Rich chocolate cake with cream', 'price': 38000, 'category': 'Desserts', 'image_name': 'mexian_tacos.png'},
        ]
        for item_data in menu_items_data:
            category_name = item_data.pop('category')
            image_name = item_data.pop('image_name', None)
            category = MenuCategory.objects.get(name=category_name)
            menu_item = MenuItem.objects.create(restaurant=restaurant, category=category, **item_data)
            
            # Set menu item image if available
            if image_name:
                image_path = os.path.join('resources/menu_images', image_name)
                if os.path.exists(image_path):
                    try:
                        with open(image_path, 'rb') as f:
                            menu_item.image.save(image_name, File(f))
                        print(f'Set image for menu item: {menu_item.name}')
                    except Exception as e:
                        print(f'Error setting image for {menu_item.name}: {e}')
                else:
                    print(f'Image not found for {menu_item.name}: {image_path}')
        print('Created 18 menu items across 6 categories.')
    else:
        print('No restaurant found to create menu items for.')
else:
    print('Menu items already exist.')
