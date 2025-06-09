from django.core.management.base import BaseCommand
from restaurants.models import MenuCategory


class Command(BaseCommand):
    help = 'Create default menu categories that restaurants can use'

    def handle(self, *args, **options):
        default_categories = [
            {'name': 'Appetizers', 'description': 'Starters and small plates', 'order': 1},
            {'name': 'Soups & Salads', 'description': 'Fresh soups and salads', 'order': 2},
            {'name': 'Main Courses', 'description': 'Main dishes and entrees', 'order': 3},
            {'name': 'Pasta & Rice', 'description': 'Pasta dishes and rice bowls', 'order': 4},
            {'name': 'Seafood', 'description': 'Fresh seafood dishes', 'order': 5},
            {'name': 'Meat & Poultry', 'description': 'Meat and chicken dishes', 'order': 6},
            {'name': 'Vegetarian', 'description': 'Vegetarian and vegan options', 'order': 7},
            {'name': 'Pizza', 'description': 'Pizza varieties', 'order': 8},
            {'name': 'Burgers & Sandwiches', 'description': 'Burgers and sandwich options', 'order': 9},
            {'name': 'Desserts', 'description': 'Sweet treats and desserts', 'order': 10},
            {'name': 'Beverages', 'description': 'Drinks and beverages', 'order': 11},
            {'name': 'Coffee & Tea', 'description': 'Hot and cold coffee and tea', 'order': 12},
        ]

        created_count = 0
        for category_data in default_categories:
            category, created = MenuCategory.objects.get_or_create(
                name=category_data['name'],
                defaults={
                    'description': category_data['description'],
                    'order': category_data['order'],
                    'is_active': True
                }
            )
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created category: {category.name}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Category already exists: {category.name}')
                )

        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {created_count} new categories')
        )