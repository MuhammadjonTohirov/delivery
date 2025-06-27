"""
Utility functions for restaurant access and permissions.
"""
from django.core.exceptions import ObjectDoesNotExist
from restaurants.models import Restaurant
from users.models import CustomUser
from typing import Optional


def get_restaurant_for_user(restaurant_id: str, user: CustomUser) -> Optional[Restaurant]:
    """
    Get a restaurant by ID with proper user permission checking.
    
    Args:
        restaurant_id: The restaurant ID to retrieve
        user: The requesting user
        
    Returns:
        Restaurant object if found and user has access, None otherwise
        
    Raises:
        Restaurant.DoesNotExist: If restaurant not found or user lacks permission
    """
    try:
        if user.is_staff or user.is_superuser:
            # Admin users can access any restaurant
            return Restaurant.objects.get(id=restaurant_id)
        else:
            # Regular users can only access restaurants they own
            return Restaurant.objects.get(id=restaurant_id, user=user)
    except Restaurant.DoesNotExist:
        raise Restaurant.DoesNotExist(
            "Restaurant not found or you don't have permission to access it."
        )


def filter_restaurants_for_user(user: CustomUser, queryset=None):
    """
    Filter restaurants based on user permissions.
    
    Args:
        user: The requesting user
        queryset: Optional queryset to filter, defaults to all restaurants
        
    Returns:
        Filtered queryset of restaurants the user can access
    """
    if queryset is None:
        queryset = Restaurant.objects.all()
    
    if user.is_staff or user.is_superuser:
        # Admin users can access all restaurants
        return queryset
    else:
        # Regular users can only access restaurants they own
        return queryset.filter(user=user)


def get_user_restaurants(user: CustomUser):
    """
    Get all restaurants that a user has access to.
    
    Args:
        user: The requesting user
        
    Returns:
        QuerySet of restaurants the user can access
    """
    return filter_restaurants_for_user(user)


def user_can_access_restaurant(user: CustomUser, restaurant_id: str) -> bool:
    """
    Check if a user can access a specific restaurant.
    
    Args:
        user: The requesting user
        restaurant_id: The restaurant ID to check
        
    Returns:
        True if user can access the restaurant, False otherwise
    """
    try:
        get_restaurant_for_user(restaurant_id, user)
        return True
    except Restaurant.DoesNotExist:
        return False