from users.models import CustomUser, RestaurantProfile
from restaurants.models import Restaurant
from django.core.files import File
import os

# Check if user exists and create restaurant
if CustomUser.objects.filter(email='rest@mail.ru').exists():
    user = CustomUser.objects.get(email='rest@mail.ru')
    
    # Create RestaurantProfile if it doesn't exist
    if not RestaurantProfile.objects.filter(user=user).exists():
        RestaurantProfile.objects.create(
            user=user,
            business_name='The Tasty Spoon',
            business_address='456 Oak Ave, Anytown, USA'
        )
        print('Restaurant profile created.')
    else:
        print('Restaurant profile already exists.')
    
    # Create Restaurant if it doesn't exist
    if not Restaurant.objects.filter(user=user).exists():
        restaurant = Restaurant.objects.create(
            user=user,
            name='The Tasty Spoon',
            description='A delightful restaurant serving authentic Italian cuisine with a modern twist. We pride ourselves on using fresh, locally sourced ingredients to create memorable dining experiences.',
            cuisine_type='Italian',
            price_range='$$',
            address='456 Oak Ave',
            city='Anytown',
            state='California',
            zip_code='12345',
            country='United States',
            delivery_radius=8.0,
            delivery_fee=15000.00,
            minimum_order=50000.00,
            primary_phone='+1-555-123-4567',
            email='contact@thetastyspoon.com',
            website='https://www.thetastyspoon.com',
            tagline='Authentic Italian, Modern Experience',
            story='Founded in 2020, The Tasty Spoon brings the authentic flavors of Italy to your doorstep. Our chef, with over 15 years of experience in Italian cuisine, crafts each dish with passion and precision.',
            is_active=True,
            is_open=True
        )
        
        # Set logo and banner images
        try:
            # Search for logo in multiple locations
            logo_search_paths = [
                os.path.join('resources/other_images', 'rest_logo.jpg'),
                os.path.join('resources/menu_images', 'rest_logo.jpg'),
                os.path.join('resources', 'rest_logo.jpg'),
            ]
            
            # Search for banner in multiple locations
            banner_search_paths = [
                os.path.join('resources/other_images', 'rest_banner.jpg'),
                os.path.join('resources/menu_images', 'rest_banner.jpg'),
                os.path.join('resources', 'rest_banner.jpg'),
            ]
            
            # Also search in subdirectories
            for root_dir in ['resources/other_images', 'resources/menu_images', 'resources']:
                if os.path.exists(root_dir):
                    for subdir in os.listdir(root_dir):
                        subdir_path = os.path.join(root_dir, subdir)
                        if os.path.isdir(subdir_path):
                            logo_search_paths.append(os.path.join(subdir_path, 'rest_logo.jpg'))
                            banner_search_paths.append(os.path.join(subdir_path, 'rest_banner.jpg'))
            
            # Set logo
            logo_found = False
            for logo_path in logo_search_paths:
                if os.path.exists(logo_path):
                    with open(logo_path, 'rb') as f:
                        restaurant.logo.save('rest_logo.jpg', File(f))
                    print(f'Restaurant logo set successfully from: {logo_path}')
                    logo_found = True
                    break
            
            if not logo_found:
                print('Logo file not found in any location')
                
            # Set banner
            banner_found = False
            for banner_path in banner_search_paths:
                if os.path.exists(banner_path):
                    with open(banner_path, 'rb') as f:
                        restaurant.banner_image.save('rest_banner.jpg', File(f))
                    print(f'Restaurant banner set successfully from: {banner_path}')
                    banner_found = True
                    break
            
            if not banner_found:
                print('Banner file not found in any location')
                
        except Exception as e:
            print(f'Error setting restaurant images: {e}')
        
        print('Restaurant created successfully.')
    else:
        print('Restaurant already exists.')
else:
    print('User rest@mail.ru not found.')
