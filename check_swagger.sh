#!/bin/bash

echo "Checking drf-spectacular installation and configuration..."

# Check if drf-spectacular is installed
pip freeze | grep drf-spectacular
if [ $? -ne 0 ]; then
    echo "drf-spectacular is not installed. Installing it now..."
    pip install drf-spectacular
fi

# Verify the necessary imports in urls.py
echo "Checking URLs configuration..."
grep -q "SpectacularAPIView" delivery/urls.py
if [ $? -ne 0 ]; then
    echo "ERROR: SpectacularAPIView import might be missing in delivery/urls.py"
else
    echo "✓ SpectacularAPIView import found in urls.py"
fi

grep -q "api/schema/" delivery/urls.py
if [ $? -ne 0 ]; then
    echo "ERROR: API schema URL pattern might be missing in delivery/urls.py"
else
    echo "✓ API schema URL pattern found in urls.py"
fi

grep -q "api/docs/" delivery/urls.py
if [ $? -ne 0 ]; then
    echo "ERROR: API docs URL pattern might be missing in delivery/urls.py"
else
    echo "✓ API docs URL pattern found in urls.py"
fi

# Check REST Framework settings
echo "Checking REST Framework settings..."
grep -q "DEFAULT_SCHEMA_CLASS" delivery/settings.py
if [ $? -ne 0 ]; then
    echo "ERROR: DEFAULT_SCHEMA_CLASS setting might be missing in settings.py"
else
    echo "✓ DEFAULT_SCHEMA_CLASS setting found in settings.py"
fi

# Check if spectacular settings are configured
echo "Checking SPECTACULAR_SETTINGS..."
grep -q "SPECTACULAR_SETTINGS" delivery/settings.py
if [ $? -ne 0 ]; then
    echo "ERROR: SPECTACULAR_SETTINGS might be missing in settings.py"
else
    echo "✓ SPECTACULAR_SETTINGS found in settings.py"
fi

# Verify drf-spectacular is in INSTALLED_APPS
grep -q "'drf_spectacular'," delivery/settings.py
if [ $? -ne 0 ]; then
    echo "ERROR: drf_spectacular might not be in INSTALLED_APPS in settings.py"
else
    echo "✓ drf_spectacular found in INSTALLED_APPS"
fi

echo "Spectacular configuration check complete."
echo "You should be able to access the API docs at: http://127.0.0.1:8000/api/docs/"
echo "If you're still having issues, try running: python manage.py spectacular --file schema.yml"
