#!/bin/bash

# Clean up remaining migration directories
apps=("cart" "geography" "notifications" "payments" "promotions" "webapp")

for app in "${apps[@]}"; do
    if [ -d "$app/migrations" ]; then
        echo "Cleaning $app migrations..."
        mv "$app/migrations" "migration_backup_$app" 2>/dev/null || true
        mkdir -p "$app/migrations"
        echo "# Empty init file for migrations" > "$app/migrations/__init__.py"
    fi
done

echo "All migration directories cleaned!"
