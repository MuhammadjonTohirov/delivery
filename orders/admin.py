from django.contrib import admin
from django.utils.html import format_html
from .models import Order, OrderItem, OrderStatusUpdate


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 1
    readonly_fields = ('id', 'unit_price', 'subtotal')
    fields = ('menu_item', 'quantity', 'unit_price', 'subtotal', 'notes')


class OrderStatusUpdateInline(admin.TabularInline):
    model = OrderStatusUpdate
    extra = 0
    readonly_fields = ('id', 'created_at')
    fields = ('status', 'updated_by', 'notes', 'created_at')


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer', 'restaurant', 'status', 'total_price', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('id', 'customer__email', 'customer__full_name', 'restaurant__name')
    readonly_fields = ('id', 'created_at', 'updated_at', 'total_price')
    inlines = [OrderItemInline, OrderStatusUpdateInline]
    fieldsets = (
        (None, {
            'fields': ('id', 'customer', 'restaurant', 'status')
        }),
        ('Delivery Details', {
            'fields': ('delivery_address', 'delivery_lat', 'delivery_lng', 'estimated_delivery_time')
        }),
        ('Payment Details', {
            'fields': ('delivery_fee', 'discount', 'total_price')
        }),
        ('Additional Information', {
            'fields': ('notes',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        """Override save to recalculate total_price after saving"""
        super().save_model(request, obj, form, change)
        # Recalculate total price after all inline items are saved
        if obj.items.exists():
            obj.total_price = obj.calculate_total_price()
            obj.save()
    
    def save_formset(self, request, form, formset, change):
        """Override to recalculate total_price after saving order items"""
        super().save_formset(request, form, formset, change)
        if formset.model == OrderItem:
            # Recalculate total price after order items are saved
            order = form.instance
            order.total_price = order.calculate_total_price()
            order.save()


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'order', 'menu_item', 'quantity', 'unit_price', 'subtotal')
    list_filter = ('order__status',)
    search_fields = ('order__id', 'menu_item__name')
    readonly_fields = ('id', 'subtotal')


@admin.register(OrderStatusUpdate)
class OrderStatusUpdateAdmin(admin.ModelAdmin):
    list_display = ('id', 'order', 'status', 'updated_by', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('order__id', 'updated_by__email', 'notes')
    readonly_fields = ('id', 'created_at')