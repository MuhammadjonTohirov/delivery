# Dashboard API Documentation

This document describes the API endpoints available for the restaurant dashboard functionality.

## Overview

The dashboard APIs provide the following functionality:
- **Statistics**: Get orders count, revenue, and average order price
- **Recent Orders**: Get a filtered list of recent orders
- **Restaurant Filter**: Get list of restaurants for filtering (admin only)

All endpoints support filtering by:
- Restaurant (required for restaurant owners, optional for admins)
- Date range (single date or date range)
- Order status

## Authentication

All endpoints require authentication. The user must be logged in and have appropriate permissions:
- **Restaurant Owners**: Can only access data for their own restaurant
- **Admins**: Can access data for all restaurants and filter by specific restaurants

## Endpoints

### 1. Dashboard Statistics

**Endpoint**: `GET /api/orders/dashboard/statistics/`

**Description**: Get dashboard statistics including orders count, revenue, and average order price.

**Query Parameters**:
- `restaurant_id` (UUID, optional): Filter by restaurant ID
  - Required for restaurant owners (must match their restaurant)
  - Optional for admins (can filter by any restaurant)
- `date_from` (Date, optional): Start date for filtering (YYYY-MM-DD format)
- `date_to` (Date, optional): End date for filtering (YYYY-MM-DD format)
- `status` (String, optional): Filter by order status
  - Valid values: `PLACED`, `CONFIRMED`, `PREPARING`, `READY_FOR_PICKUP`, `PICKED_UP`, `ON_THE_WAY`, `DELIVERED`, `CANCELLED`

**Response Example**:
```json
{
    "orders_count": 120,
    "revenue": 2400.00,
    "average_order_price": 20.00
}
```

**Usage Examples**:

1. **Restaurant owner getting today's statistics**:
   ```
   GET /api/orders/dashboard/statistics/?date_from=2024-07-26&date_to=2024-07-26
   ```

2. **Admin getting statistics for a specific restaurant and status**:
   ```
   GET /api/orders/dashboard/statistics/?restaurant_id=123e4567-e89b-12d3-a456-426614174000&status=DELIVERED
   ```

3. **Get statistics for a date range**:
   ```
   GET /api/orders/dashboard/statistics/?date_from=2024-07-01&date_to=2024-07-31
   ```

### 2. Dashboard Recent Orders

**Endpoint**: `GET /api/orders/dashboard/recent-orders/`

**Description**: Get recent orders list with filtering and pagination for dashboard.

**Query Parameters**:
- `restaurant_id` (UUID, optional): Filter by restaurant ID
- `date_from` (Date, optional): Start date for filtering (YYYY-MM-DD format)
- `date_to` (Date, optional): End date for filtering (YYYY-MM-DD format)
- `status` (String, optional): Filter by order status
- `limit` (Integer, optional): Number of orders to return (default: 10, max: 100)
- `offset` (Integer, optional): Number of orders to skip (for pagination)

**Response Example**:
```json
{
    "count": 150,
    "results": [
        {
            "id": "12345678-1234-5678-9012-123456789012",
            "customer": {
                "id": "87654321-4321-8765-2109-876543210987",
                "full_name": "Sophia Clark",
                "email": "sophia@example.com"
            },
            "restaurant": {
                "id": "11111111-2222-3333-4444-555555555555",
                "name": "Restaurant A"
            },
            "status": "DELIVERED",
            "total_price": "25.00",
            "delivery_fee": "3.00",
            "created_at": "2024-07-26T10:30:00Z",
            "updated_at": "2024-07-26T11:15:00Z",
            "item_count": 3
        },
        {
            "id": "12345678-1234-5678-9012-123456789013",
            "customer": {
                "id": "87654321-4321-8765-2109-876543210988",
                "full_name": "Ethan Miller",
                "email": "ethan@example.com"
            },
            "restaurant": {
                "id": "11111111-2222-3333-4444-555555555555",
                "name": "Restaurant A"
            },
            "status": "PREPARING",
            "total_price": "30.00",
            "delivery_fee": "3.00",
            "created_at": "2024-07-26T10:45:00Z",
            "updated_at": "2024-07-26T10:50:00Z",
            "item_count": 2
        }
    ]
}
```

**Usage Examples**:

1. **Get first 10 recent orders**:
   ```
   GET /api/orders/dashboard/recent-orders/
   ```

2. **Get next 10 orders (pagination)**:
   ```
   GET /api/orders/dashboard/recent-orders/?offset=10&limit=10
   ```

3. **Filter by status and date**:
   ```
   GET /api/orders/dashboard/recent-orders/?status=DELIVERED&date_from=2024-07-26
   ```

### 3. Dashboard Restaurants (Admin Only)

**Endpoint**: `GET /api/orders/dashboard/restaurants/`

**Description**: Get list of restaurants for dashboard filtering. Only available for admin users.

**Query Parameters**: None

**Response Example**:
```json
[
    {
        "id": "11111111-2222-3333-4444-555555555555",
        "name": "Restaurant A"
    },
    {
        "id": "22222222-3333-4444-5555-666666666666",
        "name": "Restaurant B"
    },
    {
        "id": "33333333-4444-5555-6666-777777777777",
        "name": "Pizza Palace"
    }
]
```

## Frontend Integration

### Dashboard Filter Implementation

Based on the provided dashboard image, here's how to integrate these APIs:

1. **Restaurant Filter Dropdown**:
   - For admins: Call `/api/orders/dashboard/restaurants/` to populate dropdown
   - For restaurant owners: Use their own restaurant as default (no API call needed)

2. **Date Filter**:
   - "Today" button: Set `date_from` and `date_to` to current date
   - Custom date range: Allow user to select `date_from` and `date_to`

3. **Status Filter**:
   - Dropdown with options: `PLACED`, `CONFIRMED`, `PREPARING`, `READY_FOR_PICKUP`, `PICKED_UP`, `ON_THE_WAY`, `DELIVERED`, `CANCELLED`

4. **Dashboard Cards**:
   - Call `/api/orders/dashboard/statistics/` with current filters
   - Display `orders_count`, `revenue`, and `average_order_price`

5. **Recent Orders Table**:
   - Call `/api/orders/dashboard/recent-orders/` with current filters
   - Display order ID, customer name, date, status, and total
   - Implement pagination using `offset` and `limit`

### Sample JavaScript Integration

```javascript
// Get dashboard statistics
async function getDashboardStats(filters = {}) {
    const params = new URLSearchParams(filters);
    const response = await fetch(`/api/orders/dashboard/statistics/?${params}`, {
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
        }
    });
    return response.json();
}

// Get recent orders
async function getRecentOrders(filters = {}, page = 0, limit = 10) {
    const params = new URLSearchParams({
        ...filters,
        offset: page * limit,
        limit: limit
    });
    const response = await fetch(`/api/orders/dashboard/recent-orders/?${params}`, {
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
        }
    });
    return response.json();
}

// Example usage
const filters = {
    restaurant_id: 'restaurant-uuid',
    date_from: '2024-07-26',
    status: 'DELIVERED'
};

// Update dashboard
const stats = await getDashboardStats(filters);
const orders = await getRecentOrders(filters, 0, 10);

// Update UI
document.getElementById('orders-count').textContent = stats.orders_count;
document.getElementById('revenue').textContent = `$${stats.revenue}`;
document.getElementById('avg-order').textContent = `$${stats.average_order_price}`;
```

## Error Handling

All endpoints return appropriate HTTP status codes:

- `200 OK`: Success
- `400 Bad Request`: Invalid parameters (e.g., invalid date format, invalid status)
- `403 Forbidden`: Insufficient permissions
- `401 Unauthorized`: Not authenticated

Error response format:
```json
{
    "error": "Error message describing the issue"
}
```

## Order Status Values

The following order statuses are available for filtering:

- `PLACED`: Order has been placed by customer
- `CONFIRMED`: Order confirmed by restaurant
- `PREPARING`: Order is being prepared
- `READY_FOR_PICKUP`: Order is ready for pickup
- `PICKED_UP`: Order has been picked up by driver
- `ON_THE_WAY`: Order is on the way to customer
- `DELIVERED`: Order has been delivered
- `CANCELLED`: Order has been cancelled

## Rate Limiting

Consider implementing rate limiting for these endpoints in production to prevent abuse, especially for the statistics endpoint which may involve complex database queries.

## Caching

For better performance, consider implementing caching for:
- Restaurant list (changes infrequently)
- Statistics data (can be cached for short periods)

## Security Notes

- All endpoints require authentication
- Restaurant owners can only access their own data
- Admin users have full access
- Input validation is performed on all parameters
- SQL injection protection is built-in through Django ORM