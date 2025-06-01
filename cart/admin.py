from django.contrib import admin
from .models import Cart, CartItem, SavedCart, CartPromotion, CartAbandonment


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    readonly_fields = ('subtotal',)


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('user', 'restaurant', 'total_items', 'subtotal', 'is_active', 'created_at')
    list_filter = ('is_active', 'restaurant', 'created_at')
    search_fields = ('user__email', 'user__full_name', 'restaurant__name')
    readonly_fields = ('id', 'total_items', 'subtotal', 'estimated_delivery_fee', 'total', 'created_at', 'updated_at')
    inlines = [CartItemInline]
    
    fieldsets = (
        (None, {
            'fields': ('id', 'user', 'restaurant', 'is_active')
        }),
        ('Delivery Details', {
            'fields': ('delivery_address', 'delivery_lat', 'delivery_lng', 'delivery_instructions')
        }),
        ('Totals', {
            'fields': ('total_items', 'subtotal', 'estimated_delivery_fee', 'total')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('cart', 'menu_item', 'quantity', 'unit_price', 'subtotal')
    list_filter = ('cart__restaurant', 'created_at')
    search_fields = ('cart__user__email', 'menu_item__name')
    readonly_fields = ('id', 'subtotal', 'created_at', 'updated_at')


@admin.register(SavedCart)
class SavedCartAdmin(admin.ModelAdmin):
    list_display = ('user', 'name', 'restaurant', 'is_favorite', 'times_reordered', 'created_at')
    list_filter = ('is_favorite', 'restaurant', 'created_at')
    search_fields = ('user__email', 'user__full_name', 'name', 'restaurant__name')
    readonly_fields = ('id', 'times_reordered', 'created_at', 'updated_at')


@admin.register(CartPromotion)
class CartPromotionAdmin(admin.ModelAdmin):
    list_display = ('cart', 'promotion', 'discount_amount', 'applied_at')
    list_filter = ('applied_at',)
    search_fields = ('cart__user__email', 'promotion__code', 'promotion__name')
    readonly_fields = ('applied_at',)


@admin.register(CartAbandonment)
class CartAbandonmentAdmin(admin.ModelAdmin):
    list_display = ('user', 'restaurant', 'items_count', 'cart_value', 'abandonment_stage', 'recovered', 'abandoned_at')
    list_filter = ('abandonment_stage', 'recovered', 'restaurant', 'abandoned_at')
    search_fields = ('user__email', 'user__full_name', 'restaurant__name', 'session_key')
    readonly_fields = ('created_at',)
    date_hierarchy = 'abandoned_at'
