#!/bin/sh

# Handle initial migrations
echo "Handling migrations..."
python manage.py showmigrations

# Check if there's any migration issue
if [ $? -ne 0 ]; then
  echo "Migration issues detected. Trying first-time setup..."
  find ./users -path "*/migrations/*.py" -not -name "__init__.py" -delete
  find ./users -path "*/migrations/*.pyc" -delete

  find ./core -path "*/migrations/*.py" -not -name "__init__.py" -delete
  find ./core -path "*/migrations/*.pyc" -delete

  find ./restaurants -path "*/migrations/*.py" -not -name "__init__.py" -delete
  find ./restaurants -path "*/migrations/*.pyc" -delete

  find ./orders -path "*/migrations/*.py" -not -name "__init__.py" -delete
  find ./orders -path "*/migrations/*.pyc" -delete

  find ./drivers -path "*/migrations/*.py" -not -name "__init__.py" -delete
  find ./drivers -path "*/migrations/*.pyc" -delete
  
  # Make migrations for each app in order
  python manage.py makemigrations users
  python manage.py makemigrations core
  python manage.py makemigrations restaurants
  python manage.py makemigrations orders
  python manage.py makemigrations drivers
fi

echo "Applying database migrations..."
python manage.py migrate

if [ $? -ne 0 ]; then
  echo "Migration failed! Not creating superuser."
  exit 1
fi

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Create superuser if doesn't exist
echo "Creating superuser..."
python -c "
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'delivery.settings')
import django
django.setup()
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(email='admin@example.com').exists():
    User.objects.create_superuser('admin@example.com', 'adminpassword', full_name='Admin User', role='ADMIN')
"
# Start server
echo "Starting server..."
exec python manage.py runserver 0.0.0.0:8000