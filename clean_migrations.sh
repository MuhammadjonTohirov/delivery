#!/bin/bash

# Script to clean up migration files
echo "Cleaning up migration files..."

# Remove migration files from each app
apps=("users" "restaurants" "orders" "drivers" "analytics" "cart" "geography" "notifications" "payments" "promotions" "webapp")

for app in "${apps[@]}"; do
    echo "Cleaning migrations for $app..."
    find "$app/migrations" -name "*.py" ! -name "__init__.py" -delete 2>/dev/null || true
    find "$app/migrations" -name "*.pyc" -delete 2>/dev/null || true
    find "$app/migrations/__pycache__" -name "*.pyc" -delete 2>/dev/null || true
    rmdir "$app/migrations/__pycache__" 2>/dev/null || true
done

echo "Migration cleanup complete!"
