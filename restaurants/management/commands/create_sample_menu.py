from django.core.management.base import BaseCommand
from restaurants.models import MenuCategory, MenuItem, Restaurant
from users.models import User


class Command(BaseCommand):
    help = 'Create sample menu data for testing'

    def handle(self, *args, **options):
        # Create menu categories
        categories_data = [
            {'name': 'Burgers', 'description': 'Delicious burgers and sandwiches', 'order': 1},
            {'name': 'Pizza', 'description': 'Fresh pizzas with various toppings', 'order': 2},
            {'name': 'Tacos', 'description': 'Authentic Mexican tacos', 'order': 3},
            {'name': 'Pasta', 'description': 'Italian pasta dishes', 'order': 4},
            {'name': 'Salads', 'description': 'Fresh and healthy salads', 'order': 5},
        ]

        categories = {}
        for cat_data in categories_data:
            category, created = MenuCategory.objects.get_or_create(
                name=cat_data['name'],
                defaults=cat_data
            )
            categories[cat_data['name']] = category
            if created:
                self.stdout.write(f"Created category: {category.name}")

        # Create sample menu items
        sample_items = [
            {
                'name': 'Spicy Chicken Burger',
                'description': 'Juicy chicken patty with a spicy kick, topped with fresh veggies and our special sauce.',
                'price': '12.99',
                'category': 'Burgers'
            },
            {
                'name': 'Veggie Delight Pizza',
                'description': 'A delicious pizza loaded with fresh vegetables and a blend of cheeses.',
                'price': '15.99',
                'category': 'Pizza'
            },
            {
                'name': 'Classic Beef Tacos',
                'description': 'Three soft tacos filled with seasoned ground beef, lettuce, cheese, and salsa.',
                'price': '10.99',
                'category': 'Tacos'
            },
            {
                'name': 'Creamy Tomato Pasta',
                'description': 'Pasta tossed in a rich and creamy tomato sauce, garnished with fresh basil.',
                'price': '14.99',
                'category': 'Pasta'
            },
            {
                'name': 'Fresh Garden Salad',
                'description': 'A refreshing mix of greens, tomatoes, cucumbers, and carrots with a light vinaigrette.',
                'price': '8.99',
                'category': 'Salads'
            },
            {
                'name': 'BBQ Bacon Burger',
                'description': 'Beef patty with crispy bacon, BBQ sauce, onion rings, and cheese.',
                'price': '13.99',
                'category': 'Burgers'
            },
            {
                'name': 'Margherita Pizza',
                'description': 'Classic pizza with fresh mozzarella, tomatoes, and basil leaves.',
                'price': '13.99',
                'category': 'Pizza'
            },
            {
                'name': 'Fish Tacos',
                'description': 'Grilled fish with cabbage slaw, avocado, and cilantro lime sauce.',
                'price': '12.99',
                'category': 'Tacos'
            },
            {
                'name': 'Chicken Alfredo',
                'description': 'Creamy alfredo pasta with grilled chicken breast and parmesan cheese.',
                'price': '16.99',
                'category': 'Pasta'
            },
            {
                'name': 'Caesar Salad',
                'description': 'Romaine lettuce with caesar dressing, croutons, and parmesan cheese.',
                'price': '9.99',
                'category': 'Salads'
            }
        ]

        # Get the first restaurant for adding menu items
        try:
            restaurant = Restaurant.objects.first()
            if not restaurant:
                self.stdout.write(self.style.WARNING('No restaurants found. Please create a restaurant first.'))
                return
        except Restaurant.DoesNotExist:
            self.stdout.write(self.style.WARNING('No restaurants found. Please create a restaurant first.'))
            return

        # Create menu items
        for item_data in sample_items:
            category_name = item_data.pop('category')
            category = categories.get(category_name)
            
            menu_item, created = MenuItem.objects.get_or_create(
                restaurant=restaurant,
                name=item_data['name'],
                defaults={
                    **item_data,
                    'category': category,
                    'is_available': True,
                    'is_featured': False
                }
            )
            
            if created:
                self.stdout.write(f"Created menu item: {menu_item.name}")

        self.stdout.write(self.style.SUCCESS('Successfully created sample menu data!'))
