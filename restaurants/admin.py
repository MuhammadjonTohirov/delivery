from django.contrib import admin
from .models import Restaurant, MenuCategory, MenuItem, RestaurantReview


class MenuItemInline(admin.TabularInline):
    model = MenuItem
    extra = 1
    fields = ('name', 'price', 'is_available', 'is_featured')


@admin.register(Restaurant)
class RestaurantAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'address', 'is_open', 'created_at')
    list_filter = ('is_open', 'created_at')
    search_fields = ('name', 'address', 'user__email', 'user__full_name')
    readonly_fields = ('id', 'created_at', 'updated_at')
    inlines = [MenuItemInline]
    fieldsets = (
        (None, {
            'fields': ('id', 'user', 'name', 'address')
        }),
        ('Location', {
            'fields': ('location_lat', 'location_lng')
        }),
        ('Details', {
            'fields': ('description', 'logo', 'is_open', 'opening_time', 'closing_time')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(MenuCategory)
class MenuCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'order', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name',)
    readonly_fields = ('id', 'created_at', 'updated_at')
    ordering = ('order', 'name')


@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'restaurant', 'category', 'price', 'is_available', 'is_featured')
    list_filter = ('restaurant', 'category', 'is_available', 'is_featured')
    search_fields = ('name', 'restaurant__name', 'category__name')
    readonly_fields = ('id', 'created_at', 'updated_at')
    fieldsets = (
        (None, {
            'fields': ('id', 'restaurant', 'category', 'name')
        }),
        ('Details', {
            'fields': ('description', 'price', 'image', 'preparation_time')
        }),
        ('Status', {
            'fields': ('is_available', 'is_featured')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(RestaurantReview)
class RestaurantReviewAdmin(admin.ModelAdmin):
    list_display = ('restaurant', 'user', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('restaurant__name', 'user__email', 'user__full_name', 'comment')
    readonly_fields = ('id', 'created_at', 'updated_at')