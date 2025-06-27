from django.contrib import admin
from .models import ApplicationSettings


@admin.register(ApplicationSettings)
class ApplicationSettingsAdmin(admin.ModelAdmin):
    list_display = ('app_name', 'default_currency', 'default_delivery_fee', 'updated_at')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Basic Settings', {
            'fields': ('app_name',)
        }),
        ('Currency & Pricing', {
            'fields': ('default_currency', 'default_delivery_fee', 'minimum_order_amount')
        }),
        ('Business Settings', {
            'fields': ('commission_percentage',)
        }),
        ('Contact Information', {
            'fields': ('support_email', 'support_phone')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        # Only allow adding if no settings exist
        return not ApplicationSettings.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        # Don't allow deletion of settings
        return False