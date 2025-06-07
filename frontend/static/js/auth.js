/**
 * Core Authentication JavaScript
 * Handles login, registration, and token management
 */

class AuthManager {
    constructor() {
        this.baseURL = '/api';
        this.accessToken = localStorage.getItem('accessToken');
        this.refreshToken = localStorage.getItem('refreshToken');
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
     * Get authorization headers
     */
    getAuthHeaders() {
        const headers = {
            'Content-Type': 'application/json',
        };

        if (this.accessToken) {
            headers['Authorization'] = `Bearer ${this.accessToken}`;
        }

        return headers;
    }

    /**
     * Make authenticated API request
     */
    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const config = {
            headers: this.getAuthHeaders(),
            ...options
        };

        try {
            let response = await fetch(url, config);

            // Handle token expiration
            if (response.status === 401 && this.refreshToken) {
                try {
                    await this.refreshAccessToken();
                    
                    // Retry the original request with new token
                    config.headers = this.getAuthHeaders();
                    response = await fetch(url, config);
                } catch (refreshError) {
                    this.clearTokens();
                    throw new Error('Authentication failed');
                }
            }

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || errorData.message || `HTTP ${response.status}`);
            }

            // Handle empty responses (204 No Content)
            if (response.status === 204) {
                return null;
            }

            return await response.json();
        } catch (error) {
            throw error;
        }
    }

    /**
     * Refresh access token
     */
    async refreshAccessToken() {
        if (!this.refreshToken) {
            throw new Error('No refresh token available');
        }

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
            return newAccessToken;
        } catch (error) {
            this.clearTokens();
            throw error;
        }
    }

    /**
     * Register new user
     */
    async register(email, password, fullName, role = 'CUSTOMER') {
        try {
            const response = await fetch(`${this.baseURL}/users/register/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    email: email,
                    password: password,
                    full_name: fullName,
                    role: role
                }),
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || errorData.message || 'Registration failed');
            }

            return await response.json();
        } catch (error) {
            throw error;
        }
    }

    /**
     * Login user
     */
    async login(email, password) {
        try {
            const response = await fetch(`${this.baseURL}/users/token/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    email: email,
                    password: password
                }),
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || errorData.message || 'Login failed');
            }

            const data = await response.json();
            this.setTokens(data.access, data.refresh);
            
            return data;
        } catch (error) {
            throw error;
        }
    }

    /**
     * Logout user
     */
    logout() {
        this.clearTokens();
        return Promise.resolve();
    }

    /**
     * Get current user profile
     */
    async getProfile() {
        return this.request('/users/profile/');
    }

    /**
     * Update user profile
     */
    async updateProfile(data) {
        return this.request('/users/profile/', {
            method: 'PATCH',
            body: JSON.stringify(data)
        });
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
}

// Create global auth instance
window.auth = new AuthManager();

// Utility functions for common tasks
window.authUtils = {
    /**
     * Check if user has specific role
     */
    async hasRole(role) {
        try {
            const profile = await window.auth.getProfile();
            return profile.role === role;
        } catch (error) {
            return false;
        }
    },

    /**
     * Redirect based on user role
     */
    async redirectByRole() {
        try {
            const profile = await window.auth.getProfile();
            const roleRedirects = {
                'CUSTOMER': '/api/docs/',
                'DRIVER': '/api/docs/',
                'RESTAURANT': '/api/docs/',
                'ADMIN': '/admin/'
            };
            
            const redirectUrl = roleRedirects[profile.role] || '/api/docs/';
            window.location.href = redirectUrl;
        } catch (error) {
            console.error('Failed to redirect by role:', error);
        }
    },

    /**
     * Show user info
     */
    async showUserInfo() {
        try {
            const profile = await window.auth.getProfile();
            console.log('Current user:', profile);
            return profile;
        } catch (error) {
            console.log('No authenticated user');
            return null;
        }
    }
};

// Auto-check authentication status on page load
document.addEventListener('DOMContentLoaded', function() {
    if (window.auth.isAuthenticated()) {
        console.log('User is authenticated');
        window.authUtils.showUserInfo();
    } else {
        console.log('User is not authenticated');
    }
});
