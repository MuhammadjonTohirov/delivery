from django.contrib import admin
from .models import Address, DeliveryZone, LocationHistory, GeocodingCache, DeliveryRoute, ServiceArea


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ('user', 'label', 'city', 'state', 'is_default', 'is_verified', 'created_at')
    list_filter = ('is_default', 'is_verified', 'city', 'state', 'country', 'created_at')
    search_fields = ('user__email', 'user__full_name', 'street_address', 'city', 'state')
    readonly_fields = ('id', 'created_at', 'updated_at')


@admin.register(DeliveryZone)
class DeliveryZoneAdmin(admin.ModelAdmin):
    list_display = ('name', 'restaurant', 'radius_km', 'base_delivery_fee', 'is_active', 'priority')
    list_filter = ('is_active', 'restaurant', 'created_at')
    search_fields = ('name', 'restaurant__name')
    readonly_fields = ('id', 'created_at', 'updated_at')


@admin.register(LocationHistory)
class LocationHistoryAdmin(admin.ModelAdmin):
    list_display = ('user', 'activity_type', 'latitude', 'longitude', 'created_at')
    list_filter = ('activity_type', 'created_at')
    search_fields = ('user__email', 'user__full_name')
    readonly_fields = ('id', 'created_at', 'updated_at')
    date_hierarchy = 'created_at'


@admin.register(GeocodingCache)
class GeocodingCacheAdmin(admin.ModelAdmin):
    list_display = ('original_address', 'city', 'state', 'provider', 'is_exact_match', 'created_at')
    list_filter = ('provider', 'is_exact_match', 'created_at')
    search_fields = ('original_address', 'formatted_address', 'city', 'state')
    readonly_fields = ('address_hash', 'created_at')


@admin.register(DeliveryRoute)
class DeliveryRouteAdmin(admin.ModelAdmin):
    list_display = ('driver', 'status', 'total_distance_km', 'estimated_duration_minutes', 'created_at')
    list_filter = ('status', 'optimization_algorithm', 'created_at')
    search_fields = ('driver__user__email', 'driver__user__full_name')
    readonly_fields = ('id', 'created_at', 'updated_at')


@admin.register(ServiceArea)
class ServiceAreaAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'is_active', 'launch_date', 'radius_km')
    list_filter = ('is_active', 'launch_date', 'created_at')
    search_fields = ('name', 'code')
    readonly_fields = ('created_at', 'updated_at')
