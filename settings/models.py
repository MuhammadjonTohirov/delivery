from django.db import models
from django.core.validators import MinLengthValidator


class ApplicationSettings(models.Model):
    """
    Application-wide settings model.
    This should only have one instance in the database.
    """
    CURRENCY_CHOICES = [
        ('USD', 'US Dollar ($)'),
        ('EUR', 'Euro (€)'),
        ('GBP', 'British Pound (£)'),
        ('CAD', 'Canadian Dollar (C$)'),
        ('AUD', 'Australian Dollar (A$)'),
        ('JPY', 'Japanese Yen (¥)'),
        ('CNY', 'Chinese Yuan (¥)'),
        ('INR', 'Indian Rupee (₹)'),
        ('BRL', 'Brazilian Real (R$)'),
        ('MXN', 'Mexican Peso ($)'),
        ('UZS', 'Uzbek Som (som)'),
    ]
    
    # Basic app settings
    app_name = models.CharField(
        max_length=100,
        default="Food Delivery Platform",
        help_text="Name of the application"
    )
    
    # Currency settings
    default_currency = models.CharField(
        max_length=3,
        choices=CURRENCY_CHOICES,
        default='UZS',
        help_text="Default currency for the entire platform"
    )
    
    # Business settings
    default_delivery_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=2.99,
        help_text="Default delivery fee"
    )
    
    minimum_order_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=10.00,
        help_text="Minimum order amount"
    )
    
    # Platform settings
    commission_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=15.00,
        help_text="Platform commission percentage"
    )
    
    # Contact information
    support_email = models.EmailField(
        default="support@fooddelivery.com",
        help_text="Support email address"
    )
    
    support_phone = models.CharField(
        max_length=20,
        blank=True,
        help_text="Support phone number"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Application Settings"
        verbose_name_plural = "Application Settings"
        
    def __str__(self):
        return f"App Settings - {self.app_name}"
    
    def save(self, *args, **kwargs):
        # Ensure only one instance exists
        if not self.pk and ApplicationSettings.objects.exists():
            raise ValueError('Only one ApplicationSettings instance is allowed')
        super().save(*args, **kwargs)
    
    @classmethod
    def get_settings(cls):
        """Get the application settings instance, create if doesn't exist"""
        settings, created = cls.objects.get_or_create(defaults={})
        return settings
    
    def get_currency_symbol(self):
        """Get the currency symbol for the default currency"""
        currency_symbols = {
            'USD': '$',
            'EUR': '€',
            'GBP': '£',
            'CAD': 'C$',
            'AUD': 'A$',
            'JPY': '¥',
            'CNY': '¥',
            'INR': '₹',
            'BRL': 'R$',
            'MXN': '$',
            'UZS': 'uzs',  # Use 'uzs' instead of 'som' for consistency
        }
        return currency_symbols.get(self.default_currency, 'uzs')