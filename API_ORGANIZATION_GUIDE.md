# API Organization Guide

This document describes how the Delivery Platform APIs have been organized into logical sections for better documentation and developer experience.

## Overview

The APIs have been reorganized from a single "api" section into five logical sections that group related functionality together. This makes it easier for developers to find and understand the available endpoints.

## API Sections

### 1. Authentication & User Management
**Base URL:** `/api/auth/`

This section handles all user-related operations including authentication, registration, and profile management.

**Endpoints:**
- `POST /api/auth/token/` - Login to obtain JWT token
- `POST /api/auth/token/refresh/` - Refresh JWT token
- `POST /api/auth/logout/` - Logout and invalidate refresh token
- `POST /api/auth/register/` - Register a new user
- `GET/PUT/PATCH /api/auth/profile/` - User profile management
- `POST /api/auth/change-password/` - Change user password
- `GET /api/auth/customers/` - List customers (Admin only)
- `GET /api/auth/drivers/` - List drivers (Admin only)
- `GET /api/auth/restaurant-owners/` - List restaurant owners (Admin only)

### 2. Core Business Operations
**Base URLs:** `/api/restaurants/`, `/api/orders/`, `/api/cart/`

This section contains the core business functionality including restaurant management, menu items, orders, and shopping cart operations.

**Restaurant Endpoints:**
- `GET /api/restaurants/list/` - List all restaurants
- `POST /api/restaurants/list/` - Create restaurant
- `GET/PUT/PATCH /api/restaurants/list/{id}/` - Restaurant details and management
- `GET /api/restaurants/categories/` - Menu categories
- `GET /api/restaurants/menu-items/` - Menu items
- `GET /api/restaurants/reviews/` - Restaurant reviews
- `GET /api/restaurants/statistics/` - Restaurant statistics

**Order Endpoints:**
- `GET /api/orders/` - List orders (filtered by user role)
- `POST /api/orders/` - Create new order
- `GET/PUT/PATCH /api/orders/{id}/` - Order details and management
- `GET /api/orders/dashboard/statistics/` - Dashboard statistics
- `GET /api/orders/dashboard/recent-orders/` - Recent orders
- `GET /api/orders/dashboard/restaurants/` - Restaurant dashboard data

**Cart Endpoints:**
- `GET /api/cart/` - Get cart contents
- `POST /api/cart/` - Add items to cart
- `PUT/PATCH /api/cart/{item_id}/` - Update cart items
- `DELETE /api/cart/{item_id}/` - Remove items from cart

### 3. Delivery & Logistics
**Base URLs:** `/api/drivers/`, `/api/geography/`

This section handles driver management, location tracking, and delivery route optimization.

**Driver Endpoints:**
- `GET /api/drivers/locations/` - List driver locations
- `POST /api/drivers/locations/` - Create location update
- `GET /api/drivers/availability/` - Driver availability
- `GET /api/drivers/tasks/` - Driver tasks
- `GET /api/drivers/earnings/` - Driver earnings

**Geography Endpoints:**
- `GET /api/geography/addresses/` - Address management
- `GET /api/geography/routes/` - Delivery routes
- `GET /api/geography/location-history/` - Location history
- `GET /api/geography/utils/` - Geography utilities

### 4. Financial Operations
**Base URLs:** `/api/payments/`, `/api/promotions/`

This section manages payment processing, transaction management, and promotional campaigns.

**Payment Endpoints:**
- `GET /api/payments/` - List payments
- `POST /api/payments/` - Process payment
- `GET /api/payments/{id}/` - Payment details

**Promotion Endpoints:**
- `GET /api/promotions/` - List promotions
- `POST /api/promotions/` - Create promotion
- `GET/PUT/PATCH /api/promotions/{id}/` - Promotion management

### 5. Communication & Analytics
**Base URLs:** `/api/notifications/`, `/api/analytics/`

This section handles notifications, messaging, and business analytics & reporting.

**Notification Endpoints:**
- `GET /api/notifications/` - List notifications
- `POST /api/notifications/` - Send notification
- `GET /api/notifications/preferences/` - Notification preferences
- `GET /api/notifications/push-tokens/` - Push token management

**Analytics Endpoints:**
- `GET /api/analytics/events/` - Analytics events
- `GET /api/analytics/restaurant/` - Restaurant analytics
- `GET /api/analytics/platform/` - Platform analytics
- `GET /api/analytics/dashboard-stats/` - Dashboard statistics
- `GET /api/analytics/revenue/` - Revenue metrics
- `GET /api/analytics/customer-insights/` - Customer insights
- `GET /api/analytics/popular-items/` - Popular menu items

## Implementation Details

### URL Structure Changes
The main change was reorganizing the URL structure from:
```
/api/users/ -> /api/auth/
/api/restaurants/ -> /api/restaurants/ (unchanged)
/api/orders/ -> /api/orders/ (unchanged)
/api/drivers/ -> /api/drivers/ (unchanged)
/api/payments/ -> /api/payments/ (unchanged)
/api/promotions/ -> /api/promotions/ (unchanged)
/api/notifications/ -> /api/notifications/ (unchanged)
/api/geography/ -> /api/geography/ (unchanged)
/api/cart/ -> /api/cart/ (unchanged)
/api/analytics/ -> /api/analytics/ (unchanged)
```

### Swagger Documentation Tags
Each API endpoint is now tagged with one of the five logical sections:
- `Authentication & User Management`
- `Core Business Operations`
- `Delivery & Logistics`
- `Financial Operations`
- `Communication & Analytics`

### Configuration Files Modified
1. **`delivery/urls.py`** - Updated URL patterns with logical grouping and comments
2. **`delivery/settings.py`** - Added SPECTACULAR_SETTINGS with tags and preprocessing hooks
3. **`delivery/schema_hooks.py`** - Custom preprocessing hook for automatic tag assignment
4. **View files** - Added explicit tags to ViewSets and API views

## Benefits

1. **Better Organization** - APIs are grouped by functionality rather than technical implementation
2. **Improved Developer Experience** - Easier to find relevant endpoints
3. **Clear Documentation** - Swagger UI now shows logical sections with descriptions
4. **Maintainability** - Easier to understand and maintain the API structure
5. **Scalability** - New endpoints can be easily categorized into existing sections

## Migration Notes

- All existing endpoints remain functional with the same HTTP methods and parameters
- Only the base URL for user-related endpoints changed from `/api/users/` to `/api/auth/`
- Client applications need to update user authentication endpoints to use `/api/auth/` instead of `/api/users/`
- All other endpoints remain unchanged

## Accessing the Documentation

- **Swagger UI:** http://localhost:8000/api/docs/
- **ReDoc:** http://localhost:8000/api/redoc/
- **OpenAPI Schema:** http://localhost:8000/api/schema/