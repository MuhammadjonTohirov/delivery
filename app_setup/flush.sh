#!/bin/bash

# Script to flush database and reset for fresh initialization
echo "====================================================="
echo "        Database Flush Script"
echo "====================================================="

# Exit immediately if a command exits with a non-zero status.
set -e

# Activate virtual environment (if exists)
if [ -f .venv/bin/activate ]; then
    . .venv/bin/activate
    echo "Virtual environment activated"
else
    echo "No virtual environment found, continuing without activation"
fi

echo "Flushing database..."
python manage.py flush --noinput

echo "Removing migration files (keeping __init__.py)..."
# Remove migration files from each app
apps=("users" "restaurants" "orders" "drivers" "analytics" "cart" "geography" "notifications" "payments" "promotions" "settings" "webapp")

for app in "${apps[@]}"; do
    if [ -d "$app/migrations" ]; then
        echo "Cleaning migrations for $app..."
        find "$app/migrations" -name "*.py" ! -name "__init__.py" -delete 2>/dev/null || true
        find "$app/migrations" -name "*.pyc" -delete 2>/dev/null || true
        find "$app/migrations/__pycache__" -name "*.pyc" -delete 2>/dev/null || true
        rmdir "$app/migrations/__pycache__" 2>/dev/null || true
    fi
done

echo "Removing media files..."
if [ -d "media" ]; then
    rm -rf media/*
    echo "Media files removed"
fi

echo "Creating fresh migrations..."
python manage.py makemigrations users
python manage.py makemigrations restaurants  
python manage.py makemigrations orders
python manage.py makemigrations drivers
python manage.py makemigrations analytics
python manage.py makemigrations cart
python manage.py makemigrations geography
python manage.py makemigrations notifications
python manage.py makemigrations payments
python manage.py makemigrations promotions
python manage.py makemigrations settings
python manage.py makemigrations webapp

echo "Applying fresh migrations..."
python manage.py migrate

echo "====================================================="
echo "        Database Flush Complete!"
echo "        Ready for fresh initialization"
echo "====================================================="