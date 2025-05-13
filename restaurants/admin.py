from django.contrib import admin
from .models import Restaurant, MenuCategory, MenuItem, RestaurantReview


class MenuCategoryInline(admin.TabularInline):
    model = MenuCategory
    extra = 1
    fields = ('name', 'description', 'order')
    readonly_fields = ('id',)
    show_change_link = True


class MenuItemInline(admin.TabularInline):
    model = MenuItem
    extra = 1
    fields = ('name', 'price', 'is_available', 'is_featured', 'preparation_time')
    readonly_fields = ('id', 'created_at', 'updated_at')
    show_change_link = True


class RestaurantReviewInline(admin.TabularInline):
    model = RestaurantReview
    extra = 0
    fields = ('user', 'rating', 'comment', 'created_at')
    readonly_fields = ('id', 'user', 'created_at', 'updated_at')
    can_delete = False
    show_change_link = True


@admin.register(Restaurant)
class RestaurantAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'address', 'is_open', 'average_rating', 'created_at')
    list_filter = ('is_open', 'created_at')
    search_fields = ('name', 'address', 'user__email', 'user__full_name')
    readonly_fields = ('id', 'created_at', 'updated_at')
    raw_id_fields = ('user',)
    inlines = [MenuCategoryInline, MenuItemInline, RestaurantReviewInline]
    list_editable = ('is_open',)
    date_hierarchy = 'created_at'
    
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
    
    def average_rating(self, obj):
        reviews = obj.reviews.all()
        if reviews:
            return round(sum(review.rating for review in reviews) / reviews.count(), 1)
        return "No reviews"
    average_rating.short_description = 'Avg. Rating'


@admin.register(MenuCategory)
class MenuCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'restaurant', 'order', 'item_count')
    list_filter = ('restaurant',)
    search_fields = ('name', 'restaurant__name')
    readonly_fields = ('id',)
    inlines = [MenuItemInline]
    list_editable = ('order',)
    
    def item_count(self, obj):
        return obj.items.count()
    item_count.short_description = 'Items'


@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'restaurant', 'category', 'price', 'is_available', 'is_featured')
    list_filter = ('restaurant', 'category', 'is_available', 'is_featured', 'created_at')
    search_fields = ('name', 'description', 'restaurant__name', 'category__name')
    readonly_fields = ('id', 'created_at', 'updated_at')
    list_editable = ('is_available', 'is_featured', 'price')
    date_hierarchy = 'created_at'
    
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
    list_filter = ('rating', 'created_at', 'restaurant')
    search_fields = ('restaurant__name', 'user__email', 'user__full_name', 'comment')
    readonly_fields = ('id', 'created_at', 'updated_at')
    raw_id_fields = ('restaurant', 'user')
    date_hierarchy = 'created_at'
    
    fieldsets = (
        (None, {
            'fields': ('id', 'restaurant', 'user', 'rating')
        }),
        ('Content', {
            'fields': ('comment',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )