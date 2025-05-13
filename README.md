# Getting Started with Delivery Platform

This guide will help you set up and run the Delivery Platform project using SQLite3 for simplicity.

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Virtual environment tool (optional but recommended)

## Setup Steps

1. **Clone the repository**

```bash
git clone <repository-url>
cd delivery_platform
```

2. **Create and activate a virtual environment (optional)**

```bash
# Using venv
python -m venv venv
# On Windows
venv\Scripts\activate
# On macOS/Linux
source venv/bin/activate
```

3. **Install dependencies**

```bash
pip install -r requirements.txt
```

4. **Create a .env file**

Copy the .env.example file to .env:

```bash
cp .env.example .env
```

5. **Set up the database**

If this is your first run, create migrations and apply them:

```bash
python manage.py makemigrations users
python manage.py makemigrations core
python manage.py makemigrations restaurants
python manage.py makemigrations orders
python manage.py makemigrations drivers
python manage.py migrate
```

6. **Create a superuser**

```bash
python manage.py createsuperuser
```

7. **Run the development server**

```bash
python manage.py runserver
```

The API will be available at http://127.0.0.1:8000/

## Accessing the API

- API Documentation: http://127.0.0.1:8000/api/docs/
- Admin Interface: http://127.0.0.1:8000/admin/

## Using Docker (Optional)

If you prefer to use Docker:

```bash
docker-compose build
docker-compose up
```

## Troubleshooting

If you encounter migration issues, refer to the `MIGRATION_GUIDE.md` file for troubleshooting steps.
