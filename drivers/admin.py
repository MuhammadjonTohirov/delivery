from django.contrib import admin
from .models import DriverLocation, DriverAvailability, DriverTask, DriverEarning


@admin.register(DriverLocation)
class DriverLocationAdmin(admin.ModelAdmin):
    list_display = ('driver', 'latitude', 'longitude', 'timestamp')
    list_filter = ('driver', 'timestamp')
    search_fields = ('driver__user__full_name', 'driver__user__email')
    readonly_fields = ('id', 'timestamp')
    date_hierarchy = 'timestamp'


@admin.register(DriverAvailability)
class DriverAvailabilityAdmin(admin.ModelAdmin):
    list_display = ('driver', 'status', 'last_update')
    list_filter = ('status', 'last_update')
    search_fields = ('driver__user__full_name', 'driver__user__email')
    readonly_fields = ('id', 'last_update')


@admin.register(DriverTask)
class DriverTaskAdmin(admin.ModelAdmin):
    list_display = ('driver', 'order', 'status', 'assigned_at', 'completed_at')
    list_filter = ('status', 'assigned_at', 'accepted_at', 'completed_at')
    search_fields = ('driver__user__full_name', 'order__id', 'notes')
    readonly_fields = ('id', 'assigned_at', 'accepted_at', 'picked_up_at', 'completed_at')
    date_hierarchy = 'assigned_at'
    fieldsets = (
        (None, {
            'fields': ('id', 'driver', 'order', 'status')
        }),
        ('Timestamps', {
            'fields': ('assigned_at', 'accepted_at', 'picked_up_at', 'completed_at')
        }),
        ('Additional Information', {
            'fields': ('notes',)
        }),
    )


@admin.register(DriverEarning)
class DriverEarningAdmin(admin.ModelAdmin):
    list_display = ('driver', 'order', 'amount', 'is_bonus', 'timestamp')
    list_filter = ('is_bonus', 'timestamp')
    search_fields = ('driver__user__full_name', 'order__id', 'description')
    readonly_fields = ('id', 'timestamp')
    date_hierarchy = 'timestamp'