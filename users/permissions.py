from rest_framework import permissions


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object or admins to view/edit it.
    """
    
    def has_object_permission(self, request, view, obj):
        # Admin permissions
        if request.user.is_staff or request.user.is_admin_user():
            return True
            
        # Check if the object has a user attribute
        if hasattr(obj, 'user'):
            return obj.user == request.user
            
        # If it's a user object itself
        return obj == request.user


class IsCustomer(permissions.BasePermission):
    """
    Permission check for Customer role.
    """
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_customer()


class IsDriver(permissions.BasePermission):
    """
    Permission check for Driver role.
    """
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_driver()


class IsRestaurantOwner(permissions.BasePermission):
    """
    Permission check for Restaurant Owner role.
    """
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_restaurant_owner()


class IsAdminUser(permissions.BasePermission):
    """
    Permission check for Admin role.
    """
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_admin_user()


class IsCustomerOrRestaurantOwner(permissions.BasePermission):
    """
    Permission check for users who can be either customers or restaurant owners.
    Useful for features that both customers and restaurant owners can access.
    """
    
    def has_permission(self, request, view):
        return (request.user and request.user.is_authenticated and
                (request.user.is_customer() or request.user.is_restaurant_owner()))