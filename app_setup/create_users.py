from django.contrib.auth import get_user_model

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
if not User.objects.filter(email='customer1@mail.ru').exists():
    User.objects.create_user('customer1@mail.ru', '123', full_name='Customer One')
    print('Customer 1 created.')
else:
    print('Customer 1 already exists.')

# Customer 2
if not User.objects.filter(email='customer2@mail.ru').exists():
    User.objects.create_user('customer2@mail.ru', '123', full_name='Customer Two')
    print('Customer 2 created.')
else:
    print('Customer 2 already exists.')

# Courier User
if not User.objects.filter(email='courier@mail.ru').exists():
    User.objects.create_user('courier@mail.ru', '123', full_name='Courier User')
    print('Courier user created.')
else:
    print('Courier user already exists.')