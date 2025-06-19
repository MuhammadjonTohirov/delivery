from rest_framework import serializers
from .models import ApplicationSettings


class ApplicationSettingsSerializer(serializers.ModelSerializer):
    currency_symbol = serializers.CharField(source='get_currency_symbol', read_only=True)
    
    class Meta:
        model = ApplicationSettings
        fields = [
            'id',
            'app_name',
            'default_currency',
            'currency_symbol',
            'default_delivery_fee',
            'minimum_order_amount',
            'commission_percentage',
            'support_email',
            'support_phone',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'currency_symbol']


class PublicSettingsSerializer(serializers.ModelSerializer):
    """Public settings that can be exposed to frontend without authentication"""
    currency_symbol = serializers.CharField(source='get_currency_symbol', read_only=True)
    
    class Meta:
        model = ApplicationSettings
        fields = [
            'app_name',
            'default_currency',
            'currency_symbol',
            'default_delivery_fee',
            'minimum_order_amount',
            'support_email',
        ]