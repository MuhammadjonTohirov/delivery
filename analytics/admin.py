from django.contrib import admin
from .models import AnalyticsEvent, DashboardStats, RevenueMetrics, CustomerInsights, PopularMenuItems


@admin.register(AnalyticsEvent)
class AnalyticsEventAdmin(admin.ModelAdmin):
    list_display = ('event_type', 'user', 'restaurant', 'created_at')
    list_filter = ('event_type', 'created_at', 'restaurant')
    search_fields = ('user__email', 'user__full_name', 'restaurant__name')
    readonly_fields = ('id', 'created_at', 'updated_at')
    date_hierarchy = 'created_at'


@admin.register(DashboardStats)
class DashboardStatsAdmin(admin.ModelAdmin):
    list_display = ('restaurant', 'date', 'total_orders', 'total_revenue', 'created_at')
    list_filter = ('date', 'restaurant')
    search_fields = ('restaurant__name',)
    readonly_fields = ('id', 'created_at', 'updated_at')
    date_hierarchy = 'date'


@admin.register(RevenueMetrics)
class RevenueMetricsAdmin(admin.ModelAdmin):
    list_display = ('restaurant', 'date', 'hour', 'gross_revenue', 'net_revenue')
    list_filter = ('date', 'restaurant')
    search_fields = ('restaurant__name',)
    readonly_fields = ('id', 'created_at', 'updated_at')
    date_hierarchy = 'date'


@admin.register(CustomerInsights)
class CustomerInsightsAdmin(admin.ModelAdmin):
    list_display = ('customer', 'restaurant', 'total_orders', 'total_spent', 'last_order_date')
    list_filter = ('restaurant', 'last_order_date')
    search_fields = ('customer__email', 'customer__full_name', 'restaurant__name')
    readonly_fields = ('id', 'created_at', 'updated_at')


@admin.register(PopularMenuItems)
class PopularMenuItemsAdmin(admin.ModelAdmin):
    list_display = ('menu_item', 'restaurant', 'date', 'order_count', 'total_revenue')
    list_filter = ('date', 'restaurant')
    search_fields = ('menu_item__name', 'restaurant__name')
    readonly_fields = ('id', 'created_at', 'updated_at')
    date_hierarchy = 'date'
