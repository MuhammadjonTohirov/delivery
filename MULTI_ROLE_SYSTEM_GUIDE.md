# Multi-Role User System Implementation Guide

## Overview

The delivery application has been upgraded from a single-role user system to a flexible multi-role system. This allows users to have multiple roles simultaneously, addressing the real-world scenario where a person could be both a customer (ordering food) and a restaurant owner (running their own restaurant).

## Problem Solved

**Previous Issue**: The old system forced users to choose only one role (CUSTOMER, DRIVER, RESTAURANT, or ADMIN). This was problematic because:
- A restaurant owner couldn't order food from other restaurants as a customer
- A driver couldn't own a restaurant
- Users had to create multiple accounts for different purposes

**Solution**: The new multi-role system allows users to have any combination of roles, providing a more flexible and realistic user experience.

## Technical Changes

### 1. Database Schema Changes

#### New Model: `UserRole`
```python
class UserRole(models.Model):
    name = models.CharField(max_length=15, choices=ROLE_CHOICES, unique=True)
    display_name = models.CharField(max_length=50)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
```

#### Updated User Model
- **Removed**: `role` field (CharField)
- **Added**: `roles` field (ManyToManyField to UserRole)

### 2. New User Methods

The `CustomUser` model now includes these convenience methods:

```python
# Check if user has a specific role
user.has_role('CUSTOMER')  # Returns True/False

# Get all role names for a user
user.get_role_names()  # Returns ['CUSTOMER', 'RESTAURANT']

# Convenience methods
user.is_customer()
user.is_driver()
user.is_restaurant_owner()
user.is_admin_user()

# Backward compatibility (returns first role)
user.role  # Property for legacy code
```

### 3. Updated Permissions

New permission classes have been added:

```python
# Multiple role permissions
class HasAnyRole(permissions.BasePermission):
    # Usage: Set required_roles = ['CUSTOMER', 'RESTAURANT'] on view

class HasAllRoles(permissions.BasePermission):
    # Requires user to have ALL specified roles

class IsCustomerOrRestaurantOwner(permissions.BasePermission):
    # Common combination permission
```

### 4. Migration Strategy

The migration preserves existing data by:
1. Creating the new `UserRole` model
2. Creating default role records
3. Converting existing single roles to many-to-many relationships
4. Removing the old role field

## Usage Examples

### 1. User Registration with Multiple Roles

```python
# Register a user who is both a customer and restaurant owner
data = {
    "email": "john@example.com",
    "full_name": "John Doe",
    "password": "securepass123",
    "password_confirm": "securepass123",
    "roles": ["CUSTOMER", "RESTAURANT"],
    "customer_profile": {"default_address": "123 Main St"},
    "restaurant_profile": {
        "business_name": "John's Pizza",
        "business_address": "456 Business Ave"
    }
}
```

### 2. Checking User Roles in Views

```python
# Old way (deprecated but still works for backward compatibility)
if request.user.role == 'CUSTOMER':
    # Handle customer logic

# New way (recommended)
if request.user.has_role('CUSTOMER'):
    # Handle customer logic

# Check multiple roles
if request.user.has_role('CUSTOMER') and request.user.has_role('RESTAURANT'):
    # User can both order food and manage a restaurant
```

### 3. Permission Classes

```python
# Single role permission
class MyView(APIView):
    permission_classes = [IsCustomer]

# Multiple role permission
class MyView(APIView):
    permission_classes = [HasAnyRole]
    required_roles = ['CUSTOMER', 'RESTAURANT']

# Combined permission
class MyView(APIView):
    permission_classes = [IsCustomerOrRestaurantOwner]
```

### 4. Filtering Querysets by Role

```python
# Get all users with customer role
customers = User.objects.filter(roles__name='CUSTOMER').distinct()

# Get users with multiple roles
customer_restaurant_owners = User.objects.filter(
    roles__name__in=['CUSTOMER', 'RESTAURANT']
).annotate(
    role_count=Count('roles')
).filter(role_count=2).distinct()
```

## API Changes

### 1. User Registration Endpoint

**New Field**: `roles` (array of role names)

```json
{
  "email": "user@example.com",
  "full_name": "User Name",
  "password": "password123",
  "password_confirm": "password123",
  "roles": ["CUSTOMER", "RESTAURANT"],
  "customer_profile": {...},
  "restaurant_profile": {...}
}
```

### 2. User Profile Response

**New Fields**:
- `roles`: Array of role objects with name and display_name
- `role_names`: Array of role names for convenience

```json
{
  "id": "uuid",
  "email": "user@example.com",
  "full_name": "User Name",
  "roles": [
    {"name": "CUSTOMER", "display_name": "Customer"},
    {"name": "RESTAURANT", "display_name": "Restaurant Owner"}
  ],
  "role_names": ["CUSTOMER", "RESTAURANT"],
  "customer_profile": {...},
  "restaurant_profile": {...}
}
```

### 3. JWT Token Claims

**Updated Claims**:
- `roles`: Array of role names
- `role`: First role (for backward compatibility)

## Admin Interface Changes

### 1. User Admin
- **Updated**: Role filter now works with many-to-many relationship
- **Added**: Role display shows all user roles
- **Enhanced**: Profile inlines show based on user's roles

### 2. New UserRole Admin
- Manage available roles in the system
- Enable/disable roles
- Update role display names and descriptions

## Backward Compatibility

The system maintains backward compatibility through:

1. **Property Access**: `user.role` still works (returns first role)
2. **Token Claims**: JWT tokens still include `role` claim
3. **Migration**: Existing data is preserved and converted

## Best Practices

### 1. Role Checking
```python
# ✅ Recommended
if user.has_role('CUSTOMER'):
    # Handle customer logic

# ❌ Deprecated (but still works)
if user.role == 'CUSTOMER':
    # Handle customer logic
```

### 2. Permission Design
```python
# ✅ Use specific permission classes
class CustomerOnlyView(APIView):
    permission_classes = [IsCustomer]

# ✅ Use flexible multi-role permissions
class FlexibleView(APIView):
    permission_classes = [HasAnyRole]
    required_roles = ['CUSTOMER', 'RESTAURANT']
```

### 3. Profile Management
```python
# ✅ Check role before accessing profile
if user.has_role('RESTAURANT') and hasattr(user, 'restaurant_profile'):
    restaurant = user.restaurant_profile

# ✅ Handle multiple profiles
profiles = []
if user.has_role('CUSTOMER'):
    profiles.append(user.customer_profile)
if user.has_role('RESTAURANT'):
    profiles.append(user.restaurant_profile)
```

## Testing

### 1. Create Test Users with Multiple Roles
```python
def test_multi_role_user():
    user = User.objects.create_user(
        email='test@example.com',
        full_name='Test User',
        password='testpass123'
    )
    
    # Add multiple roles
    customer_role = UserRole.objects.get(name='CUSTOMER')
    restaurant_role = UserRole.objects.get(name='RESTAURANT')
    user.roles.add(customer_role, restaurant_role)
    
    assert user.has_role('CUSTOMER')
    assert user.has_role('RESTAURANT')
    assert not user.has_role('DRIVER')
```

### 2. Test Permission Classes
```python
def test_multi_role_permissions():
    # Test that user with multiple roles can access appropriate endpoints
    # Test that permission classes work correctly with new role system
```

## Migration Notes

1. **Data Preservation**: All existing user roles are preserved
2. **Default Roles**: System creates default role records automatically
3. **Profile Creation**: Existing profiles remain intact
4. **Rollback**: Migration includes reverse operations for rollback

## Future Enhancements

1. **Role Hierarchy**: Implement role inheritance (e.g., ADMIN inherits all permissions)
2. **Dynamic Permissions**: Role-based permission assignment
3. **Role Expiration**: Time-limited roles
4. **Role Approval**: Admin approval for certain role assignments

## Troubleshooting

### Common Issues

1. **AttributeError: 'CustomUser' object has no attribute 'role'**
   - Solution: Run migrations to update database schema

2. **Permission Denied Errors**
   - Solution: Update permission classes to use new role checking methods

3. **Missing Profiles**
   - Solution: Ensure signals are properly connected to create profiles for new roles

### Debug Commands

```bash
# Check user roles
python manage.py shell
>>> from users.models import CustomUser
>>> user = CustomUser.objects.get(email='user@example.com')
>>> print(user.get_role_names())

# Verify role records exist
>>> from users.models import UserRole
>>> print(UserRole.objects.all())
```

## Conclusion

The multi-role system provides a more flexible and realistic approach to user management in the delivery application. It allows users to have multiple roles simultaneously while maintaining backward compatibility with existing code.

The implementation includes proper data migration, comprehensive permission classes, and maintains API compatibility while adding new functionality.