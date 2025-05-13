from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from .models import CustomUser, CustomerProfile, DriverProfile, RestaurantProfile


class CustomerProfileInline(admin.StackedInline):
    model = CustomerProfile
    can_delete = False
    verbose_name_plural = 'Customer Profile'
    fk_name = 'user'
    fields = ('default_address', 'default_location_lat', 'default_location_lng')


class DriverProfileInline(admin.StackedInline):
    model = DriverProfile
    can_delete = False
    verbose_name_plural = 'Driver Profile'
    fk_name = 'user'
    fields = ('vehicle_type', 'license_number')


class RestaurantProfileInline(admin.StackedInline):
    model = RestaurantProfile
    can_delete = False
    verbose_name_plural = 'Restaurant Profile'
    fk_name = 'user'
    fields = ('business_name', 'business_address', 'business_registration_number')


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ('email', 'full_name', 'role', 'is_active', 'is_staff', 'date_joined')
    list_filter = ('role', 'is_active', 'is_staff', 'date_joined')
    search_fields = ('email', 'full_name', 'phone')
    ordering = ('email',)
    readonly_fields = ('date_joined', 'last_login')
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Personal info'), {'fields': ('full_name', 'phone')}),
        (_('Permissions'), {'fields': ('role', 'is_active', 'is_staff', 'is_superuser',
                                       'groups', 'user_permissions')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'full_name', 'password1', 'password2', 'role', 'is_active', 'is_staff'),
        }),
    )
    
    def get_inlines(self, request, obj=None):
        if obj:
            if obj.role == 'CUSTOMER':
                return [CustomerProfileInline]
            elif obj.role == 'DRIVER':
                return [DriverProfileInline]
            elif obj.role == 'RESTAURANT':
                return [RestaurantProfileInline]
        return []


@admin.register(CustomerProfile)
class CustomerProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'default_address', 'created_at', 'updated_at')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('user__email', 'user__full_name', 'default_address')
    readonly_fields = ('created_at', 'updated_at')
    raw_id_fields = ('user',)
    fieldsets = (
        (None, {
            'fields': ('user', 'default_address')
        }),
        ('Location Information', {
            'fields': ('default_location_lat', 'default_location_lng')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(DriverProfile)
class DriverProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'vehicle_type', 'license_number', 'created_at', 'updated_at')
    list_filter = ('vehicle_type', 'created_at', 'updated_at')
    search_fields = ('user__email', 'user__full_name', 'license_number')
    readonly_fields = ('created_at', 'updated_at')
    raw_id_fields = ('user',)
    fieldsets = (
        (None, {
            'fields': ('user', 'vehicle_type', 'license_number')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(RestaurantProfile)
class RestaurantProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'business_name', 'business_address', 'created_at', 'updated_at')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('user__email', 'user__full_name', 'business_name', 'business_address', 'business_registration_number')
    readonly_fields = ('created_at', 'updated_at')
    raw_id_fields = ('user',)
    fieldsets = (
        (None, {
            'fields': ('user', 'business_name', 'business_address', 'business_registration_number')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )