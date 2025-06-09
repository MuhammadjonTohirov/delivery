from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from .models import CustomUser, CustomerProfile, DriverProfile, RestaurantProfile


class CustomerProfileInline(admin.StackedInline):
    model = CustomerProfile
    can_delete = False
    verbose_name_plural = 'Customer Profile'
    fk_name = 'user'


class DriverProfileInline(admin.StackedInline):
    model = DriverProfile
    can_delete = False
    verbose_name_plural = 'Driver Profile'
    fk_name = 'user'


class RestaurantProfileInline(admin.StackedInline):
    model = RestaurantProfile
    can_delete = False
    verbose_name_plural = 'Restaurant Profile'
    fk_name = 'user'


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ('email', 'full_name', 'get_user_type', 'avatar', 'is_active', 'is_staff', 'date_joined')
    list_filter = ('is_active', 'is_staff', 'date_joined')
    search_fields = ('email', 'full_name', 'phone')
    ordering = ('email',)
    filter_horizontal = ('groups', 'user_permissions')
    
    def get_user_type(self, obj):
        """Display user type based on profiles"""
        types = []
        if obj.is_restaurant_owner():
            types.append('Restaurant Owner')
        if obj.is_driver():
            types.append('Driver')
        if obj.is_admin_user():
            types.append('Admin')
        if not types:
            types.append('Customer')
        return ', '.join(types)
    get_user_type.short_description = 'User Type'
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Personal info'), {'fields': ('full_name', 'phone', 'avatar')}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser',
                                       'groups', 'user_permissions')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'full_name', 'avatar', 'password1', 'password2', 'is_active', 'is_staff'),
        }),
    )
    
    def get_inlines(self, request, obj=None):
        """Show appropriate profile inlines based on user profiles"""
        inlines = []
        if obj:
            # Always show customer profile inline since all users are customers
            inlines.append(CustomerProfileInline)
            if obj.is_driver():
                inlines.append(DriverProfileInline)
            if obj.is_restaurant_owner():
                inlines.append(RestaurantProfileInline)
        return inlines


@admin.register(CustomerProfile)
class CustomerProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'default_address', 'created_at', 'updated_at')
    search_fields = ('user__email', 'user__full_name', 'default_address')


@admin.register(DriverProfile)
class DriverProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'vehicle_type', 'license_number', 'created_at', 'updated_at')
    search_fields = ('user__email', 'user__full_name', 'license_number')


@admin.register(RestaurantProfile)
class RestaurantProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'business_name', 'business_address', 'created_at', 'updated_at')
    search_fields = ('user__email', 'user__full_name', 'business_name', 'business_address')