from django.contrib import admin
from .models import Notification, NotificationTemplate, NotificationPreference, PushToken, NotificationLog


@admin.register(NotificationTemplate)
class NotificationTemplateAdmin(admin.ModelAdmin):
    list_display = ('type', 'title_template', 'is_active', 'send_push', 'send_email', 'created_at')
    list_filter = ('is_active', 'send_push', 'send_email', 'send_sms', 'created_at')
    search_fields = ('type', 'title_template', 'message_template')
    readonly_fields = ('id', 'created_at', 'updated_at')


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('title', 'recipient', 'priority', 'is_read', 'created_at')
    list_filter = ('priority', 'is_read', 'template__type', 'created_at')
    search_fields = ('title', 'message', 'recipient__email', 'recipient__full_name')
    readonly_fields = ('id', 'created_at', 'updated_at')
    date_hierarchy = 'created_at'
    
    fieldsets = (
        (None, {
            'fields': ('id', 'recipient', 'template', 'title', 'message', 'priority')
        }),
        ('Status', {
            'fields': ('is_read', 'read_at')
        }),
        ('Related Objects', {
            'fields': ('related_order', 'related_restaurant')
        }),
        ('Action', {
            'fields': ('action_url', 'action_text')
        }),
        ('Delivery Status', {
            'fields': ('sent_push', 'sent_email', 'sent_sms')
        }),
        ('Metadata', {
            'fields': ('metadata',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(admin.ModelAdmin):
    list_display = ('user', 'order_updates_push', 'promotions_push', 'system_updates_push', 'created_at')
    list_filter = ('order_updates_push', 'promotions_push', 'system_updates_push', 'created_at')
    search_fields = ('user__email', 'user__full_name')
    readonly_fields = ('id', 'created_at', 'updated_at')


@admin.register(PushToken)
class PushTokenAdmin(admin.ModelAdmin):
    list_display = ('user', 'device_type', 'is_active', 'last_used', 'created_at')
    list_filter = ('device_type', 'is_active', 'created_at')
    search_fields = ('user__email', 'user__full_name', 'device_id')
    readonly_fields = ('id', 'created_at')


@admin.register(NotificationLog)
class NotificationLogAdmin(admin.ModelAdmin):
    list_display = ('notification', 'delivery_method', 'status', 'provider', 'created_at')
    list_filter = ('delivery_method', 'status', 'provider', 'created_at')
    search_fields = ('notification__title', 'provider_message_id', 'error_message')
    readonly_fields = ('id', 'created_at')
    date_hierarchy = 'created_at'
