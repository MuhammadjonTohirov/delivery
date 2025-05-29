/**
 * Utility Functions - utils.js
 * Common utility functions used throughout the application
 */

const Utils = {
    /**
     * Debounce function to limit function execution frequency
     */
    debounce(func, wait, immediate = false) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                timeout = null;
                if (!immediate) func.apply(this, args);
            };
            const callNow = immediate && !timeout;
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
            if (callNow) func.apply(this, args);
        };
    },

    /**
     * Throttle function to limit function execution rate
     */
    throttle(func, limit) {
        let inThrottle;
        return function(...args) {
            if (!inThrottle) {
                func.apply(this, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    },

    /**
     * Format currency values
     */
    formatCurrency(amount, currency = 'USD', locale = 'en-US') {
        return new Intl.NumberFormat(locale, {
            style: 'currency',
            currency: currency,
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        }).format(amount || 0);
    },

    /**
     * Format numbers with locale-specific formatting
     */
    formatNumber(number, locale = 'en-US') {
        return new Intl.NumberFormat(locale).format(number || 0);
    },

    /**
     * Format date and time
     */
    formatDateTime(date, options = {}) {
        const defaultOptions = {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        };
        
        const formatOptions = { ...defaultOptions, ...options };
        const dateObj = new Date(date);
        
        return dateObj.toLocaleDateString('en-US', formatOptions);
    },

    /**
     * Format date only
     */
    formatDate(date, options = {}) {
        const defaultOptions = {
            year: 'numeric',
            month: 'short',
            day: 'numeric'
        };
        
        const formatOptions = { ...defaultOptions, ...options };
        const dateObj = new Date(date);
        
        return dateObj.toLocaleDateString('en-US', formatOptions);
    },

    /**
     * Format time only
     */
    formatTime(date, options = {}) {
        const defaultOptions = {
            hour: '2-digit',
            minute: '2-digit'
        };
        
        const formatOptions = { ...defaultOptions, ...options };
        const dateObj = new Date(date);
        
        return dateObj.toLocaleTimeString('en-US', formatOptions);
    },

    /**
     * Format relative time (time ago)
     */
    formatTimeAgo(date) {
        const now = new Date();
        const past = new Date(date);
        const diffInSeconds = Math.floor((now - past) / 1000);

        const intervals = {
            year: 31536000,
            month: 2592000,
            week: 604800,
            day: 86400,
            hour: 3600,
            minute: 60
        };

        for (const [unit, seconds] of Object.entries(intervals)) {
            const interval = Math.floor(diffInSeconds / seconds);
            if (interval >= 1) {
                return `${interval} ${unit}${interval > 1 ? 's' : ''} ago`;
            }
        }

        return 'just now';
    },

    /**
     * Validate email format
     */
    isValidEmail(email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    },

    /**
     * Validate phone number format (basic)
     */
    isValidPhone(phone) {
        const phoneRegex = /^[\+]?[1-9][\d]{0,15}$/;
        return phoneRegex.test(phone.replace(/[\s\-\(\)]/g, ''));
    },

    /**
     * Generate random ID
     */
    generateId(length = 8) {
        const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
        let result = '';
        for (let i = 0; i < length; i++) {
            result += chars.charAt(Math.floor(Math.random() * chars.length));
        }
        return result;
    },

    /**
     * Deep clone an object
     */
    deepClone(obj) {
        if (obj === null || typeof obj !== 'object') return obj;
        if (obj instanceof Date) return new Date(obj.getTime());
        if (obj instanceof Array) return obj.map(item => this.deepClone(item));
        if (typeof obj === 'object') {
            const clonedObj = {};
            for (const key in obj) {
                if (obj.hasOwnProperty(key)) {
                    clonedObj[key] = this.deepClone(obj[key]);
                }
            }
            return clonedObj;
        }
    },

    /**
     * Capitalize first letter of string
     */
    capitalize(str) {
        if (!str) return '';
        return str.charAt(0).toUpperCase() + str.slice(1).toLowerCase();
    },

    /**
     * Convert string to title case
     */
    toTitleCase(str) {
        if (!str) return '';
        return str.replace(/\w\S*/g, (txt) => 
            txt.charAt(0).toUpperCase() + txt.substr(1).toLowerCase()
        );
    },

    /**
     * Truncate text to specified length
     */
    truncateText(text, maxLength = 100, suffix = '...') {
        if (!text || text.length <= maxLength) return text;
        return text.substr(0, maxLength) + suffix;
    },

    /**
     * Format file size in human readable format
     */
    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    },

    /**
     * Get order status badge class
     */
    getOrderStatusClass(status) {
        const statusClasses = {
            'PLACED': 'status-placed',
            'CONFIRMED': 'status-confirmed',
            'PREPARING': 'status-preparing',
            'READY_FOR_PICKUP': 'status-ready',
            'ON_THE_WAY': 'status-on-way',
            'DELIVERED': 'status-delivered',
            'CANCELLED': 'status-cancelled'
        };
        
        return statusClasses[status] || 'status-default';
    },

    /**
     * Get order status display text
     */
    getOrderStatusText(status) {
        const statusTexts = {
            'PLACED': 'Order Placed',
            'CONFIRMED': 'Confirmed',
            'PREPARING': 'Preparing',
            'READY_FOR_PICKUP': 'Ready for Pickup',
            'ON_THE_WAY': 'On the Way',
            'DELIVERED': 'Delivered',
            'CANCELLED': 'Cancelled'
        };
        
        return statusTexts[status] || status;
    },

    /**
     * Get available order actions based on status
     */
    getOrderActions(status) {
        const actions = {
            'PLACED': ['confirm', 'reject'],
            'CONFIRMED': ['preparing'],
            'PREPARING': ['ready'],
            'READY_FOR_PICKUP': [],
            'ON_THE_WAY': [],
            'DELIVERED': [],
            'CANCELLED': []
        };
        
        return actions[status] || [];
    },

    /**
     * Parse URL parameters
     */
    parseUrlParams(url = window.location.search) {
        const params = new URLSearchParams(url);
        const result = {};
        for (const [key, value] of params) {
            result[key] = value;
        }
        return result;
    },

    /**
     * Build URL with parameters
     */
    buildUrl(base, params = {}) {
        const url = new URL(base, window.location.origin);
        Object.entries(params).forEach(([key, value]) => {
            if (value !== null && value !== undefined && value !== '') {
                url.searchParams.set(key, value);
            }
        });
        return url.toString();
    },

    /**
     * Download data as file
     */
    downloadFile(data, filename, type = 'application/json') {
        const blob = new Blob([data], { type });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);
    },

    /**
     * Export data to CSV
     */
    exportToCSV(data, filename = 'export.csv') {
        if (!data || data.length === 0) return;
        
        const headers = Object.keys(data[0]);
        const csvContent = [
            headers.join(','),
            ...data.map(row => 
                headers.map(header => {
                    const value = row[header];
                    return typeof value === 'string' && value.includes(',') 
                        ? `"${value}"` 
                        : value;
                }).join(',')
            )
        ].join('\n');
        
        this.downloadFile(csvContent, filename, 'text/csv');
    },

    /**
     * Copy text to clipboard
     */
    async copyToClipboard(text) {
        try {
            if (navigator.clipboard && window.isSecureContext) {
                await navigator.clipboard.writeText(text);
                return true;
            } else {
                // Fallback for older browsers
                const textArea = document.createElement('textarea');
                textArea.value = text;
                textArea.style.position = 'fixed';
                textArea.style.opacity = '0';
                document.body.appendChild(textArea);
                textArea.focus();
                textArea.select();
                const successful = document.execCommand('copy');
                document.body.removeChild(textArea);
                return successful;
            }
        } catch (error) {
            console.error('Failed to copy text: ', error);
            return false;
        }
    },

    /**
     * Scroll to element smoothly
     */
    scrollToElement(element, offset = 0) {
        const targetElement = typeof element === 'string' 
            ? document.querySelector(element) 
            : element;
            
        if (targetElement) {
            const targetPosition = targetElement.offsetTop - offset;
            window.scrollTo({
                top: targetPosition,
                behavior: 'smooth'
            });
        }
    },

    /**
     * Check if element is in viewport
     */
    isInViewport(element) {
        const rect = element.getBoundingClientRect();
        return (
            rect.top >= 0 &&
            rect.left >= 0 &&
            rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) &&
            rect.right <= (window.innerWidth || document.documentElement.clientWidth)
        );
    },

    /**
     * Local storage helpers
     */
    storage: {
        set(key, value) {
            try {
                localStorage.setItem(key, JSON.stringify(value));
                return true;
            } catch (error) {
                console.error('Failed to save to localStorage:', error);
                return false;
            }
        },

        get(key, defaultValue = null) {
            try {
                const item = localStorage.getItem(key);
                return item ? JSON.parse(item) : defaultValue;
            } catch (error) {
                console.error('Failed to read from localStorage:', error);
                return defaultValue;
            }
        },

        remove(key) {
            try {
                localStorage.removeItem(key);
                return true;
            } catch (error) {
                console.error('Failed to remove from localStorage:', error);
                return false;
            }
        },

        clear() {
            try {
                localStorage.clear();
                return true;
            } catch (error) {
                console.error('Failed to clear localStorage:', error);
                return false;
            }
        }
    },

    /**
     * Device detection
     */
    device: {
        isMobile() {
            return window.innerWidth <= 768;
        },

        isTablet() {
            return window.innerWidth > 768 && window.innerWidth <= 1024;
        },

        isDesktop() {
            return window.innerWidth > 1024;
        },

        isTouchDevice() {
            return 'ontouchstart' in window || navigator.maxTouchPoints > 0;
        }
    },

    /**
     * Color utilities
     */
    colors: {
        hexToRgb(hex) {
            const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
            return result ? {
                r: parseInt(result[1], 16),
                g: parseInt(result[2], 16),
                b: parseInt(result[3], 16)
            } : null;
        },

        rgbToHex(r, g, b) {
            return "#" + ((1 << 24) + (r << 16) + (g << 8) + b).toString(16).slice(1);
        },

        getRandomColor() {
            return '#' + Math.floor(Math.random()*16777215).toString(16);
        }
    },

    /**
     * Animation helpers
     */
    animate: {
        fadeIn(element, duration = 300) {
            element.style.opacity = 0;
            element.style.display = 'block';
            
            const start = performance.now();
            
            function animate(currentTime) {
                const elapsed = currentTime - start;
                const progress = Math.min(elapsed / duration, 1);
                
                element.style.opacity = progress;
                
                if (progress < 1) {
                    requestAnimationFrame(animate);
                }
            }
            
            requestAnimationFrame(animate);
        },

        fadeOut(element, duration = 300) {
            const start = performance.now();
            const startOpacity = parseFloat(getComputedStyle(element).opacity);
            
            function animate(currentTime) {
                const elapsed = currentTime - start;
                const progress = Math.min(elapsed / duration, 1);
                
                element.style.opacity = startOpacity * (1 - progress);
                
                if (progress < 1) {
                    requestAnimationFrame(animate);
                } else {
                    element.style.display = 'none';
                }
            }
            
            requestAnimationFrame(animate);
        }
    },

    /**
     * Form validation helpers
     */
    validation: {
        required(value) {
            return value !== null && value !== undefined && value.toString().trim() !== '';
        },

        email(value) {
            return Utils.isValidEmail(value);
        },

        phone(value) {
            return Utils.isValidPhone(value);
        },

        minLength(value, min) {
            return value && value.length >= min;
        },

        maxLength(value, max) {
            return !value || value.length <= max;
        },

        numeric(value) {
            return !isNaN(value) && !isNaN(parseFloat(value));
        },

        url(value) {
            try {
                new URL(value);
                return true;
            } catch {
                return false;
            }
        }
    }
};

// Export for module use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = Utils;
}
