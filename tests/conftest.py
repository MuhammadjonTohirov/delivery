"""Configuration file for pytest fixtures that can be shared across test files."""

import pytest
import os
import django
from django.conf import settings

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'delivery.settings')
django.setup()

# Import after Django setup
from rest_framework.test import APIClient
from django.urls import reverse

# Make sure the settings are properly loaded
settings.DATABASES['default']['ATOMIC_REQUESTS'] = True


@pytest.fixture(scope='session')
def django_db_setup():
    """Configure the Django DB for the test session."""
    settings.DATABASES['default'] = {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
        'ATOMIC_REQUESTS': True,  # Ensure atomic transactions are enabled
    }


@pytest.fixture
def api_client():
    """Return an authenticated client."""
    return APIClient()


@pytest.fixture
def user_password():
    """Return a default test password."""
    return 'testpassword123'