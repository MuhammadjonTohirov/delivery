"""
Management command to initialize application settings.
"""
from django.core.management.base import BaseCommand
from django.core.management import CommandError
from settings.models import ApplicationSettings


class Command(BaseCommand):
    help = 'Initialize application settings with default values'

    def add_arguments(self, parser):
        parser.add_argument(
            '--currency',
            type=str,
            help='Set the default currency (e.g., USD, EUR, GBP)',
            default='USD'
        )
        parser.add_argument(
            '--app-name',
            type=str,
            help='Set the application name',
            default='Food Delivery Platform'
        )
        parser.add_argument(
            '--delivery-fee',
            type=float,
            help='Set the default delivery fee',
            default=2.99
        )
        parser.add_argument(
            '--min-order',
            type=float,
            help='Set the minimum order amount',
            default=10.00
        )
        parser.add_argument(
            '--commission',
            type=float,
            help='Set the platform commission percentage',
            default=15.00
        )
        parser.add_argument(
            '--support-email',
            type=str,
            help='Set the support email address',
            default='support@fooddelivery.com'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force update settings even if they already exist'
        )

    def handle(self, *args, **options):
        try:
            # Check if settings already exist
            if ApplicationSettings.objects.exists() and not options['force']:
                self.stdout.write(
                    self.style.WARNING(
                        'Application settings already exist. Use --force to update them.'
                    )
                )
                return

            # Validate currency
            valid_currencies = [choice[0] for choice in ApplicationSettings.CURRENCY_CHOICES]
            currency = options['currency'].upper()
            if currency not in valid_currencies:
                raise CommandError(
                    f"Invalid currency '{currency}'. Valid choices: {', '.join(valid_currencies)}"
                )

            # Create or update settings
            settings, created = ApplicationSettings.objects.get_or_create(
                defaults={
                    'app_name': options['app_name'],
                    'default_currency': currency,
                    'default_delivery_fee': options['delivery_fee'],
                    'minimum_order_amount': options['min_order'],
                    'commission_percentage': options['commission'],
                    'support_email': options['support_email'],
                }
            )

            if not created and options['force']:
                # Update existing settings
                settings.app_name = options['app_name']
                settings.default_currency = currency
                settings.default_delivery_fee = options['delivery_fee']
                settings.minimum_order_amount = options['min_order']
                settings.commission_percentage = options['commission']
                settings.support_email = options['support_email']
                settings.save()

            action = 'updated' if not created else 'created'
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Application settings {action} successfully!'
                )
            )
            
            # Display current settings
            self.stdout.write('\nCurrent settings:')
            self.stdout.write(f'  App Name: {settings.app_name}')
            self.stdout.write(f'  Currency: {settings.default_currency} ({settings.get_currency_symbol()})')
            self.stdout.write(f'  Delivery Fee: {settings.get_currency_symbol()}{settings.default_delivery_fee}')
            self.stdout.write(f'  Min Order: {settings.get_currency_symbol()}{settings.minimum_order_amount}')
            self.stdout.write(f'  Commission: {settings.commission_percentage}%')
            self.stdout.write(f'  Support Email: {settings.support_email}')

            # Refresh cache
            from settings.startup import refresh_settings_cache
            refresh_settings_cache()
            self.stdout.write(self.style.SUCCESS('Settings cache refreshed.'))

        except Exception as e:
            raise CommandError(f'Error initializing settings: {e}')