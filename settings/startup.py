"""
Application settings startup and caching module.
Loads application settings on Django startup and provides cached access.
"""
import logging
from django.core.cache import cache
from django.db import OperationalError, ProgrammingError

logger = logging.getLogger(__name__)

# Cache keys
SETTINGS_CACHE_KEY = 'app_settings'
CURRENCY_CACHE_KEY = 'app_currency'
CURRENCY_SYMBOL_CACHE_KEY = 'app_currency_symbol'

# Cache timeout (in seconds) - 1 hour
CACHE_TIMEOUT = 3600


def load_application_settings():
    """
    Load application settings and cache them.
    This is called lazily when settings are first needed.
    """
    try:
        # Import here to avoid circular imports
        from .models import ApplicationSettings
        
        # Get or create application settings
        settings = ApplicationSettings.get_settings()
        
        # Cache the settings object
        cache.set(SETTINGS_CACHE_KEY, settings, CACHE_TIMEOUT)
        
        # Cache commonly used values for performance
        cache.set(CURRENCY_CACHE_KEY, settings.default_currency, CACHE_TIMEOUT)
        cache.set(CURRENCY_SYMBOL_CACHE_KEY, settings.get_currency_symbol(), CACHE_TIMEOUT)
        
        logger.info(f"Application settings loaded: Currency={settings.default_currency}")
        return settings
        
    except (OperationalError, ProgrammingError) as e:
        # This can happen during migrations or initial setup
        logger.warning(f"Could not load application settings: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error loading application settings: {e}")
        return None


def get_cached_settings():
    """
    Get application settings from cache or database.
    Returns the ApplicationSettings instance.
    """
    settings = cache.get(SETTINGS_CACHE_KEY)
    
    if settings is None:
        # Try to load settings lazily
        settings = load_application_settings()
    
    return settings


def get_cached_currency():
    """
    Get the default currency from cache or database.
    Returns the currency code (e.g., 'USD').
    """
    currency = cache.get(CURRENCY_CACHE_KEY)
    
    if currency is None:
        settings = get_cached_settings()
        if settings:
            currency = settings.default_currency
            cache.set(CURRENCY_CACHE_KEY, currency, CACHE_TIMEOUT)
        else:
            # Fallback to USD if settings can't be loaded
            currency = 'USD'
    
    return currency


def get_cached_currency_symbol():
    """
    Get the currency symbol from cache or database.
    Returns the currency symbol (e.g., '$').
    """
    symbol = cache.get(CURRENCY_SYMBOL_CACHE_KEY)
    
    if symbol is None:
        settings = get_cached_settings()
        if settings:
            symbol = settings.get_currency_symbol()
            cache.set(CURRENCY_SYMBOL_CACHE_KEY, symbol, CACHE_TIMEOUT)
        else:
            # Fallback to $ if settings can't be loaded
            symbol = '$'
    
    return symbol


def invalidate_settings_cache():
    """
    Invalidate all settings-related cache entries.
    Call this when settings are updated.
    """
    cache.delete(SETTINGS_CACHE_KEY)
    cache.delete(CURRENCY_CACHE_KEY)
    cache.delete(CURRENCY_SYMBOL_CACHE_KEY)
    logger.info("Application settings cache invalidated")


def refresh_settings_cache():
    """
    Refresh the settings cache with fresh data from database.
    """
    invalidate_settings_cache()
    load_application_settings()
    logger.info("Application settings cache refreshed")