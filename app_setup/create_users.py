from django.contrib.auth import get_user_model
from users.models import CustomerProfile

User = get_user_model()

# Superuser
if not User.objects.filter(email='main@mail.ru').exists():
    User.objects.create_superuser('main@mail.ru', '123', full_name='Main User')
    print('Superuser created.')
else:
    print('Superuser already exists.')

# Restaurant User
if not User.objects.filter(email='rest@mail.ru').exists():
    User.objects.create_user('rest@mail.ru', '123', full_name='Restaurant Owner')
    print('Restaurant user created.')
else:
    print('Restaurant user already exists.')

# Customer 1
customer1, created = User.objects.get_or_create(
    email='customer1@mail.ru',
    defaults={'full_name': 'Customer One'}
)
if created:
    customer1.set_password('123')
    customer1.save()
    print('Customer 1 created.')
else:
    print('Customer 1 already exists.')

# Create or update CustomerProfile for customer1
profile1, profile_created = CustomerProfile.objects.get_or_create(
    user=customer1,
    defaults={
        'default_location_lat': 40.384849,
        'default_location_lng': 71.781445
    }
)
if not profile_created:
    profile1.default_location_lat = 40.384849
    profile1.default_location_lng = 71.781445
    profile1.save()
    print('Customer 1 location updated.')
else:
    print('Customer 1 profile created with default location.')

# Customer 2
customer2, created = User.objects.get_or_create(
    email='customer2@mail.ru',
    defaults={'full_name': 'Customer Two'}
)
if created:
    customer2.set_password('123')
    customer2.save()
    print('Customer 2 created.')
else:
    print('Customer 2 already exists.')

# Create or update CustomerProfile for customer2
profile2, profile_created = CustomerProfile.objects.get_or_create(
    user=customer2,
    defaults={
        'default_location_lat': 40.384849,
        'default_location_lng': 71.781445
    }
)
if not profile_created:
    profile2.default_location_lat = 40.384849
    profile2.default_location_lng = 71.781445
    profile2.save()
    print('Customer 2 location updated.')
else:
    print('Customer 2 profile created with default location.')

# Courier User
if not User.objects.filter(email='courier@mail.ru').exists():
    User.objects.create_user('courier@mail.ru', '123', full_name='Courier User')
    print('Courier user created.')
else:
    print('Courier user already exists.')