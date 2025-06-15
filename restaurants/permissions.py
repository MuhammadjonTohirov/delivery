from rest_framework import permissions


class IsRestaurantOwnerOrAdmin(permissions.BasePermission):
    """
    Custom permission for restaurant operations.
    - Restaurant owners can only manage their own restaurant data
    - Admins can manage all restaurant data
    """
    
    def has_permission(self, request, view):
        """Check if user has permission to access the view"""
        if not request.user.is_authenticated:
            return False
            
        # Admin users have full access
        if request.user.is_staff:
            return True
            
        # Restaurant owners can access their own data
        if request.user.is_restaurant_owner():
            return hasattr(request.user, 'restaurant')
            
        return False
    
    def has_object_permission(self, request, view, obj):
        """Check if user has permission to access specific object"""
        # Admin users have full access
        if request.user.is_staff:
            return True
            
        # For restaurant owners, check ownership
        if request.user.is_restaurant_owner() and hasattr(request.user, 'restaurant'):
            # For restaurant objects
            if hasattr(obj, 'user'):
                return obj.user == request.user
            
            # For menu categories and items
            if hasattr(obj, 'restaurant'):
                restaurants = request.user.restaurants
                return obj.restaurant in restaurants
                
        return False


class IsRestaurantOwnerOnly(permissions.BasePermission):
    """
    Permission for restaurant-only operations (excludes admin)
    """
    
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and 
            request.user.is_restaurant_owner() and
            hasattr(request.user, 'restaurant')
        )
    
    def has_object_permission(self, request, view, obj):
        if not self.has_permission(request, view):
            return False
            
        # Check ownership
        if hasattr(obj, 'user'):
            return obj.user == request.user
        if hasattr(obj, 'restaurant'):
            return obj.restaurant == request.user.restaurant
            
        return False


class CanModifyRestaurantData(permissions.BasePermission):
    """
    Permission for modifying restaurant data (categories, menu items)
    """
    
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
            
        return (
            request.user.is_authenticated and
            (request.user.is_staff or 
             (request.user.is_restaurant_owner() and hasattr(request.user, 'restaurant')))
        )
    
    def has_object_permission(self, request, view, obj):
        # Read permissions for all authenticated users
        if request.method in permissions.SAFE_METHODS:
            return True
            
        # Write permissions
        if request.user.is_staff:
            return True
            
        if request.user.is_restaurant_owner() and hasattr(request.user, 'restaurant'):
            if hasattr(obj, 'restaurant'):
                return obj.restaurant == request.user.restaurant
                
        return False


class IsMenuCategoryOwner(permissions.BasePermission):
    """
    Permission for menu category operations.
    Since categories are now global, only staff can modify them.
    Restaurant owners can view all categories.
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
            
        # Only staff can create/modify global categories
        return request.user.is_authenticated and request.user.is_staff
    
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
            
        # Only staff can modify global categories
        return request.user.is_staff


class IsMenuItemOwner(permissions.BasePermission):
    """
    Permission to check if user owns the menu item
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
            
        return request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
            
        if request.user.is_staff:
            return True
            
        if request.user.is_restaurant_owner() and hasattr(request.user, 'restaurant'):
            return obj.restaurant == request.user.restaurant
            
        return False
