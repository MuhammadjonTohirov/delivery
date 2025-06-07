# Migration Fix - Step by Step Guide

## ✅ Completed Steps

1. **Database backup**: Moved `db.sqlite3` to `db_backup.sqlite3`
2. **Migration cleanup**: All old migration files have been backed up and new empty migration directories created

## 🚀 Next Steps (Run these commands in your terminal)

### Step 1: Create new migrations in the correct order

```bash
python manage.py makemigrations users
python manage.py makemigrations core
python manage.py makemigrations restaurants
python manage.py makemigrations orders
python manage.py makemigrations drivers
python manage.py makemigrations analytics
python manage.py makemigrations cart
python manage.py makemigrations geography
python manage.py makemigrations notifications
python manage.py makemigrations payments
python manage.py makemigrations promotions
python manage.py makemigrations webapp
```

### Step 2: Apply all migrations

```bash
python manage.py migrate
```

### Step 3: Create a superuser

```bash
python manage.py createsuperuser
```

### Step 4: Test the setup

```bash
python manage.py runserver
```

Then visit:
- http://127.0.0.1:8000/ - Main page
- http://127.0.0.1:8000/api/docs/ - API documentation
- http://127.0.0.1:8000/admin/ - Admin interface

## 📁 Backup Information

All your previous migration files have been safely backed up to:
- `migration_backup/` - Original users migrations
- `migration_backup_restaurants/` - Restaurant migrations
- `migration_backup_orders/` - Order migrations
- `migration_backup_drivers/` - Driver migrations
- `migration_backup_analytics/` - Analytics migrations
- `migration_backup_cart/` - Cart migrations
- `migration_backup_geography/` - Geography migrations
- `migration_backup_notifications/` - Notification migrations
- `migration_backup_payments/` - Payment migrations
- `migration_backup_promotions/` - Promotion migrations
- `migration_backup_webapp/` - Webapp migrations
- `db_backup.sqlite3` - Your original database

## 🔧 If You Encounter Issues

If you get any errors during migration:

1. **Check the order**: Make sure you run `makemigrations` in the exact order shown above
2. **Check models**: Ensure all your model files are correctly formatted
3. **Run step by step**: Don't run all makemigrations at once - do them one app at a time
4. **Check dependencies**: Some apps depend on others (like orders depends on restaurants)

## 🎯 Expected Result

After successful migration, you should have:
- ✅ A fresh database with all your models
- ✅ UUID primary keys working correctly
- ✅ All relationships properly established
- ✅ No datatype mismatch errors
- ✅ Clean migration history

The migration should complete without errors and you'll have a fresh, working database ready for development!
