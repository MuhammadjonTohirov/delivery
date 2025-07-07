#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

# Activate virtual environment (if exists)
if [ -f .venv/bin/activate ]; then
    . .venv/bin/activate
    echo "Virtual environment activated"
else
    echo "No virtual environment found, continuing without activation"
fi

# Run database migrations
python manage.py makemigrations
python manage.py migrate

# Run specific migration for menu category images
python manage.py migrate restaurants

# Collect static files
python manage.py collectstatic --noinput

# Initialize application settings
python manage.py init_settings --force


python manage.py shell < app_setup/create_users.py
python manage.py shell < app_setup/create_restaurant_profile.py
python manage.py shell < app_setup/create_menu_data.py
python manage.py shell < app_setup/set_user_avatars.py
