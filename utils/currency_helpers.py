"""
Currency utility functions for the application.
Uses cached settings for better performance.
"""
from decimal import Decimal


def get_default_currency():
    """Get the default currency from cached application settings"""
    try:
        from settings.startup import get_cached_currency
        return get_cached_currency()
    except:
        # Fallback if settings not available
        return 'UZS'


def get_currency_symbol():
    """Get the currency symbol for the default currency from cached settings"""
    try:
        from settings.startup import get_cached_currency_symbol
        return get_cached_currency_symbol()
    except:
        # Fallback if settings not available
        currency = get_default_currency()
        if currency == 'UZS':
            return 'uzs'
        return 'uzs'


def format_price(amount, include_symbol=True):
    """
    Format a price with the default currency
    
    Args:
        amount: The amount to format (can be string, int, float, or Decimal)
        include_symbol: Whether to include the currency symbol/code
        
    Returns:
        Formatted price string (e.g., "13 000 uzs" or "13,000.00" for USD)
    """
    if amount is None:
        amount = 0
    
    # Convert to Decimal for precise handling
    if isinstance(amount, str):
        try:
            amount = Decimal(amount)
        except:
            amount = Decimal('0')
    else:
        amount = Decimal(str(amount))
    
    currency = get_default_currency()
    
    # Special formatting for UZS (Uzbek Som) - no decimals, space separation, currency after
    if currency == 'UZS':
        # Round to nearest whole number for UZS
        whole_amount = int(round(amount))
        # Format with spaces as thousand separators
        formatted = f"{whole_amount:,}".replace(',', ' ')
        if include_symbol:
            return f"{formatted} uzs"
        return formatted
    else:
        # Standard formatting for other currencies
        formatted = f"{amount:.2f}"
        # Add thousand separators with commas for readability
        if '.' in formatted:
            integer_part, decimal_part = formatted.split('.')
            integer_part = f"{int(integer_part):,}"
            formatted = f"{integer_part}.{decimal_part}"
        
        if include_symbol:
            symbol = get_currency_symbol()
            return f"{symbol}{formatted}"
        
        return formatted


def get_currency_info():
    """Get complete currency information from cached settings"""
    return {
        'code': get_default_currency(),
        'symbol': get_currency_symbol(),
    }