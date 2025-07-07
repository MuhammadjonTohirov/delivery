from users.models import CustomUser
from django.core.files import File
import os

image_mapping = {
    'main@mail.ru': 'img_courier.png', # Assuming main user is the courier for now
    'rest@mail.ru': 'img_rest_owner.png',
    'customer1@mail.ru': 'img_customer1.png',
    'customer2@mail.ru': 'img_customer2.png',
    'courier@mail.ru': 'img_courier.png',
}

for email, image_name in image_mapping.items():
    try:
        user = CustomUser.objects.get(email=email)
        image_path = os.path.join('/Users/r/Documents/Development/Personal/Startups/delivery/server/resources/user_images', image_name)
        with open(image_path, 'rb') as f:
            user.avatar.save(image_name, File(f))
        print(f"Successfully set avatar for {email}")
    except CustomUser.DoesNotExist:
        print(f"User not found: {email}")
    except FileNotFoundError:
        print(f"Image not found for {email}: {image_name}")
    except Exception as e:
        print(f"An error occurred for {email}: {e}")
