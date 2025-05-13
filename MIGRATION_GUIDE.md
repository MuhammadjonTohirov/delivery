# Migration Troubleshooting Guide (SQLite3)

If you're experiencing migration issues, follow these steps:

## Step 1: Reset the database (if needed)

Simply delete the db.sqlite3 file from your project root:

```bash
rm db.sqlite3
```

## Step 2: Remove all existing migration files

```bash
find . -path "*/migrations/*.py" -not -name "__init__.py" -delete
find . -path "*/migrations/*.pyc" -delete
```

## Step 3: Make new migrations in the correct order

```bash
python manage.py makemigrations users
python manage.py makemigrations core
python manage.py makemigrations restaurants
python manage.py makemigrations orders  
python manage.py makemigrations drivers
```

## Step 4: Apply migrations

```bash
python manage.py migrate
```

## Step 5: Create a superuser

```bash
python manage.py createsuperuser
```

## Common Pitfalls:

1. Make sure the order of apps in INSTALLED_APPS in settings.py is correct
2. If the SQLite database file is locked, check for other processes using it
3. If issues persist, enable Django's migration debug logging:

```python
# Add to settings.py temporarily
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django.db.migrations': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    },
}
```
