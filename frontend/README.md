# Delivery Platform - Minimal Frontend

This directory contains a minimal frontend setup for the Delivery Platform API.

## Structure

```
frontend/
├── static/
│   ├── css/
│   │   └── base.css          # Basic styling
│   └── js/
│       └── auth.js           # Core authentication JavaScript
└── templates/
    ├── base.html             # Base template
    └── index.html            # API documentation index page
```

## What's Included

### JavaScript (auth.js)
- `AuthManager` class for handling authentication
- Token management (access/refresh tokens)
- Core API methods (login, register, logout)
- Authenticated request handling
- Basic utility functions

### Templates
- **base.html**: Minimal base template with CSS and JS includes
- **index.html**: API documentation landing page with links to Swagger docs

### CSS
- **base.css**: Basic responsive styling for the index page

## Usage

### Authentication in JavaScript

```javascript
// Login
try {
    const result = await window.auth.login('user@example.com', 'password');
    console.log('Login successful:', result);
} catch (error) {
    console.error('Login failed:', error.message);
}

// Register
try {
    const result = await window.auth.register('user@example.com', 'password', 'Full Name', 'CUSTOMER');
    console.log('Registration successful:', result);
} catch (error) {
    console.error('Registration failed:', error.message);
}

// Make authenticated API calls
try {
    const profile = await window.auth.getProfile();
    console.log('User profile:', profile);
} catch (error) {
    console.error('Failed to get profile:', error.message);
}

// Check if authenticated
if (window.auth.isAuthenticated()) {
    console.log('User is logged in');
}

// Logout
window.auth.logout();
```

### Building Your Frontend

You can now build any frontend framework on top of this:

1. **React/Vue/Angular SPA**: Use the AuthManager class for API communication
2. **Mobile App**: Use the same API endpoints for authentication and data
3. **Traditional HTML/JS**: Extend the existing templates and JavaScript

## API Documentation

- **Swagger UI**: http://localhost:8000/api/docs/
- **ReDoc**: http://localhost:8000/api/redoc/
- **Admin Interface**: http://localhost:8000/admin/

## Key API Endpoints

- **Authentication**: `/api/users/token/`, `/api/users/register/`
- **Restaurants**: `/api/restaurants/`
- **Orders**: `/api/orders/`
- **Cart**: `/api/cart/`
- **Analytics**: `/api/analytics/`
- **Notifications**: `/api/notifications/`

## Previous Frontend Backup

The previous complete frontend has been backed up to `../frontend_backup/frontend_old/` in case you need any reference.
