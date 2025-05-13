#!/bin/bash

# This script runs your Django application without Docker
# It's a simpler alternative if you're having Docker issues

# Create a virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate the virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Make migrations
echo "Making migrations..."
python manage.py makemigrations users
python manage.py makemigrations core
python manage.py makemigrations restaurants
python manage.py makemigrations orders
python manage.py makemigrations drivers

# Apply migrations
echo "Applying migrations..."
python manage.py migrate

# Create superuser if it doesn't exist
echo "Creating superuser if needed..."
python -c "
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'delivery.settings')
import django
django.setup()
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(email='admin@example.com').exists():
    User.objects.create_superuser('admin@example.com', 'adminpassword', full_name='Admin User', role='ADMIN')
    print('Superuser created successfully.')
else:
    print('Superuser already exists.')
"

# Start the development server
echo "Starting development server..."
echo "You can access the app at http://127.0.0.1:8000"
echo "Admin interface: http://127.0.0.1:8000/admin"
echo "API documentation: http://127.0.0.1:8000/api/docs/"
python manage.py runserver
