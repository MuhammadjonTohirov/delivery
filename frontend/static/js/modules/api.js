/**
 * API Manager Module - api.js
 * Handles all API communications with proper error handling and authentication
 */

class APIManager {
    constructor() {
        this.baseURL = '/api';
        this.accessToken = localStorage.getItem('accessToken');
        this.refreshToken = localStorage.getItem('refreshToken');
        this.isRefreshing = false;
        this.failedQueue = [];
    }

    /**
     * Set authentication tokens
     */
    setTokens(accessToken, refreshToken) {
        this.accessToken = accessToken;
        this.refreshToken = refreshToken;
        
        if (accessToken) {
            localStorage.setItem('accessToken', accessToken);
        } else {
            localStorage.removeItem('accessToken');
        }
        
        if (refreshToken) {
            localStorage.setItem('refreshToken', refreshToken);
        } else {
            localStorage.removeItem('refreshToken');
        }
    }

    /**
     * Clear authentication tokens
     */
    clearTokens() {
        this.accessToken = null;
        this.refreshToken = null;
        localStorage.removeItem('accessToken');
        localStorage.removeItem('refreshToken');
    }

    /**
     * Check if user is authenticated
     */
    isAuthenticated() {
        return !!this.accessToken;
    }

    /**
     * Get default headers for API requests
     */
    getHeaders(includeAuth = true) {
        const headers = {
            'Content-Type': 'application/json',
        };

        if (includeAuth && this.accessToken) {
            headers['Authorization'] = `Bearer ${this.accessToken}`;
        }

        return headers;
    }

    /**
     * Process failed requests queue after token refresh
     */
    processQueue(error, token = null) {
        this.failedQueue.forEach(({ resolve, reject }) => {
            if (error) {
                reject(error);
            } else {
                resolve(token);
            }
        });
        
        this.failedQueue = [];
    }

    /**
     * Refresh access token
     */
    async refreshAccessToken() {
        if (this.isRefreshing) {
            // If already refreshing, wait for it to complete
            return new Promise((resolve, reject) => {
                this.failedQueue.push({ resolve, reject });
            });
        }

        if (!this.refreshToken) {
            this.clearTokens();
            window.location.href = '/login/';
            return Promise.reject(new Error('No refresh token available'));
        }

        this.isRefreshing = true;

        try {
            const response = await fetch(`${this.baseURL}/users/token/refresh/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    refresh: this.refreshToken
                }),
            });

            if (!response.ok) {
                throw new Error('Token refresh failed');
            }

            const data = await response.json();
            const newAccessToken = data.access;

            this.setTokens(newAccessToken, this.refreshToken);
            this.processQueue(null, newAccessToken);

            return newAccessToken;
        } catch (error) {
            this.processQueue(error, null);
            this.clearTokens();
            window.location.href = '/login/';
            throw error;
        } finally {
            this.isRefreshing = false;
        }
    }

    /**
     * Make API request with automatic token refresh
     */
    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const config = {
            headers: this.getHeaders(),
            ...options
        };

        try {
            let response = await fetch(url, config);

            // Handle token expiration
            if (response.status === 401 && this.refreshToken) {
                try {
                    await this.refreshAccessToken();
                    
                    // Retry the original request with new token
                    config.headers = this.getHeaders();
                    response = await fetch(url, config);
                } catch (refreshError) {
                    throw refreshError;
                }
            }

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new APIError(
                    errorData.detail || errorData.message || `HTTP ${response.status}`,
                    response.status,
                    errorData
                );
            }

            // Handle empty responses (204 No Content)
            if (response.status === 204) {
                return null;
            }

            return await response.json();
        } catch (error) {
            if (error instanceof APIError) {
                throw error;
            }
            
            // Network or other errors
            throw new APIError(
                'Network error occurred. Please check your connection.',
                0,
                { originalError: error.message }
            );
        }
    }

    /**
     * GET request
     */
    async get(endpoint, params = {}) {
        const searchParams = new URLSearchParams();
        
        Object.entries(params).forEach(([key, value]) => {
            if (value !== null && value !== undefined && value !== '') {
                searchParams.append(key, value);
            }
        });

        const queryString = searchParams.toString();
        const url = queryString ? `${endpoint}?${queryString}` : endpoint;

        return this.request(url, { method: 'GET' });
    }

    /**
     * POST request
     */
    async post(endpoint, data = {}) {
        return this.request(endpoint, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    /**
     * PUT request
     */
    async put(endpoint, data = {}) {
        return this.request(endpoint, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    }

    /**
     * PATCH request
     */
    async patch(endpoint, data = {}) {
        return this.request(endpoint, {
            method: 'PATCH',
            body: JSON.stringify(data)
        });
    }

    /**
     * DELETE request
     */
    async delete(endpoint) {
        return this.request(endpoint, { method: 'DELETE' });
    }

    /**
     * Upload file
     */
    async upload(endpoint, formData) {
        const url = `${this.baseURL}${endpoint}`;
        
        const config = {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${this.accessToken}`
                // Don't set Content-Type for FormData, let browser set it
            },
            body: formData
        };

        try {
            const response = await fetch(url, config);

            if (response.status === 401 && this.refreshToken) {
                await this.refreshAccessToken();
                config.headers['Authorization'] = `Bearer ${this.accessToken}`;
                const retryResponse = await fetch(url, config);
                return this.handleResponse(retryResponse);
            }

            return this.handleResponse(response);
        } catch (error) {
            throw new APIError(
                'Upload failed. Please try again.',
                0,
                { originalError: error.message }
            );
        }
    }

    /**
     * Handle response for file uploads
     */
    async handleResponse(response) {
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new APIError(
                errorData.detail || `Upload failed with status ${response.status}`,
                response.status,
                errorData
            );
        }

        return response.status === 204 ? null : await response.json();
    }

    // Restaurant API Methods
    async getRestaurants(params = {}) {
        return this.get('/restaurants/list/', params);
    }

    async getRestaurant(id) {
        return this.get(`/restaurants/list/${id}/`);
    }

    async getMyRestaurant() {
        return this.get('/restaurants/list/mine/');
    }

    async updateRestaurant(id, data) {
        return this.patch(`/restaurants/list/${id}/`, data);
    }

    async getRestaurantStats(id) {
        return this.get(`/restaurants/statistics/${id}/get/`);
    }

    async getRestaurantAnalytics(id, params = {}) {
        return this.get(`/analytics/restaurant/dashboard/`, { restaurant_id: id, ...params });
    }

    // Orders API Methods
    async getOrders(params = {}) {
        return this.get('/orders/', params);
    }

    async getOrder(id) {
        return this.get(`/orders/${id}/`);
    }

    async updateOrderStatus(id, status, notes = '') {
        return this.post(`/orders/${id}/restaurant_action/`, {
            action: status,
            note: notes
        });
    }

    async markOrderReady(id, notes = '') {
        return this.post(`/orders/${id}/mark_ready_for_pickup/`, { note: notes });
    }

    async markOrderPreparing(id, notes = '') {
        return this.post(`/orders/${id}/preparing/`, { note: notes });
    }

    // Menu API Methods
    async getMenuItems(params = {}) {
        return this.get('/restaurants/menu-items/', params);
    }

    async getMenuItem(id) {
        return this.get(`/restaurants/menu-items/${id}/`);
    }

    async createMenuItem(data) {
        return this.post('/restaurants/menu-items/', data);
    }

    async updateMenuItem(id, data) {
        return this.patch(`/restaurants/menu-items/${id}/`, data);
    }

    async deleteMenuItem(id) {
        return this.delete(`/restaurants/menu-items/${id}/`);
    }

    async getMenuCategories(params = {}) {
        return this.get('/restaurants/categories/', params);
    }

    // Reviews API Methods
    async getRestaurantReviews(restaurantId) {
        return this.get(`/restaurants/list/${restaurantId}/reviews/`);
    }

    // Analytics API Methods
    async getDashboardAnalytics(params = {}) {
        return this.get('/analytics/restaurant/dashboard/', params);
    }

    // User API Methods
    async getProfile() {
        return this.get('/users/profile/');
    }

    async updateProfile(data) {
        return this.patch('/users/profile/', data);
    }

    // Notifications API Methods
    async getNotifications(params = {}) {
        return this.get('/notifications/', params);
    }

    async markNotificationRead(id) {
        return this.patch(`/notifications/${id}/`, { read: true });
    }

    async markAllNotificationsRead() {
        return this.post('/notifications/mark-all-read/');
    }
}

/**
 * Custom API Error class
 */
class APIError extends Error {
    constructor(message, status, data = {}) {
        super(message);
        this.name = 'APIError';
        this.status = status;
        this.data = data;
    }

    get isNetworkError() {
        return this.status === 0;
    }

    get isAuthError() {
        return this.status === 401 || this.status === 403;
    }

    get isValidationError() {
        return this.status === 400;
    }

    get isNotFoundError() {
        return this.status === 404;
    }

    get isServerError() {
        return this.status >= 500;
    }
}

// Export for module use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { APIManager, APIError };
}
