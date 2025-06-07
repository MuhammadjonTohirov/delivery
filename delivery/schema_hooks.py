"""
Custom schema preprocessing hooks for drf-spectacular.
This module handles the automatic tagging of API endpoints based on their URL patterns.
"""

def custom_preprocessing_hook(endpoints):
    """
    Custom preprocessing hook to assign tags to API endpoints based on URL patterns.
    This organizes the Swagger documentation into logical sections.
    """
    
    # Define URL pattern to tag mappings
    url_tag_mapping = {
        '/api/auth/': 'Authentication & User Management',
        '/api/restaurants/': 'Core Business Operations',
        '/api/orders/': 'Core Business Operations',
        '/api/cart/': 'Core Business Operations',
        '/api/drivers/': 'Delivery & Logistics',
        '/api/geography/': 'Delivery & Logistics',
        '/api/payments/': 'Financial Operations',
        '/api/promotions/': 'Financial Operations',
        '/api/notifications/': 'Communication & Analytics',
        '/api/analytics/': 'Communication & Analytics',
    }
    
    # Process each endpoint
    processed_endpoints = []
    for (path, path_regex, method, callback) in endpoints:
        # Find the appropriate tag for this endpoint
        tag = None
        for url_pattern, tag_name in url_tag_mapping.items():
            if path.startswith(url_pattern):
                tag = tag_name
                break
        
        # Only include endpoints that have been categorized
        if tag:
            # Apply tag to the callback
            if hasattr(callback, 'cls'):
                # For ViewSets and APIViews
                if not hasattr(callback.cls, 'tags'):
                    callback.cls.tags = []
                if tag not in callback.cls.tags:
                    callback.cls.tags.append(tag)
            elif hasattr(callback, 'view_class'):
                # For function-based views
                if not hasattr(callback.view_class, 'tags'):
                    callback.view_class.tags = []
                if tag not in callback.view_class.tags:
                    callback.view_class.tags.append(tag)
            
            processed_endpoints.append((path, path_regex, method, callback))
    
    return processed_endpoints