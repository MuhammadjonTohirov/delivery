// Dashboard Components - dashboard-components.js

class DashboardComponents {
    static createOrderCard(order) {
        const statusClasses = {
            'PLACED': 'placed',
            'CONFIRMED': 'confirmed', 
            'PREPARING': 'preparing',
            'READY_FOR_PICKUP': 'ready',
            'ON_THE_WAY': 'ready',
            'DELIVERED': 'delivered',
            'CANCELLED': 'cancelled'
        };

        return `
            <div class="order-card fade-in" data-order-id="${order.id}">
                <div class="order-header">
                    <div>
                        <div class="order-id">Order #${order.id.substring(0, 8)}</div>
                        <div class="order-customer">${order.customer_name}</div>
                    </div>
                    <span class="order-status ${statusClasses[order.status] || 'placed'}">
                        ${order.status.replace('_', ' ')}
                    </span>
                </div>
                <div class="order-details">
                    <div>
                        <strong>Items:</strong> ${order.item_count || order.items?.length || 0}
                    </div>
                    <div>
                        <strong>Total:</strong> $${parseFloat(order.total_price || 0).toFixed(2)}
                    </div>
                    <div>
                        <strong>Address:</strong> ${order.delivery_address}
                    </div>
                    <div>
                        <strong>Time:</strong> ${new Date(order.created_at).toLocaleString()}
                    </div>
                </div>
                ${order.notes ? `<div class="order-notes"><strong>Notes:</strong> ${order.notes}</div>` : ''}
            </div>
        `;
    }

    static createRestaurantCard(restaurant) {
        return `
            <div class="restaurant-card fade-in" data-restaurant-id="${restaurant.id}">
                <img src="${restaurant.logo || 'https://via.placeholder.com/300x160?text=No+Image'}" 
                     alt="${restaurant.name}" class="restaurant-image">
                <div class="restaurant-info">
                    <h3 class="restaurant-name">${restaurant.name}</h3>
                    <p class="restaurant-address">${restaurant.address}</p>
                    <div class="restaurant-stats">
                        <div class="restaurant-rating">
                            <i class="fas fa-star"></i>
                            ${restaurant.average_rating || 'No ratings'}
                        </div>
                        <div class="restaurant-status ${restaurant.is_open ? 'open' : 'closed'}">
                            ${restaurant.is_open ? 'Open' : 'Closed'}
                        </div>
                    </div>
                    <div class="restaurant-actions">
                        <button class="btn-primary" onclick="editRestaurant('${restaurant.id}')">
                            <i class="fas fa-edit"></i> Edit
                        </button>
                    </div>
                </div>
            </div>
        `;
    }

    static createReviewCard(review) {
        const stars = Array.from({length: 5}, (_, i) => 
            `<span class="star ${i < review.rating ? '' : 'empty'}"></span>`
        ).join('');

        return `
            <div class="review-card fade-in">
                <img src="${review.user_avatar || 'https://via.placeholder.com/48x48'}" 
                     alt="${review.user_full_name}" class="review-avatar">
                <div class="review-content">
                    <div class="review-header">
                        <div class="reviewer-name">${review.user_full_name}</div>
                        <div class="review-date">${this.formatDate(review.created_at)}</div>
                    </div>
                    <div class="review-text">${review.comment || 'No comment provided'}</div>
                    <div class="review-rating">
                        <div class="stars">${stars}</div>
                        <span class="rating-score">${review.rating}.0</span>
                    </div>
                </div>
                ${review.food_image ? `<img src="${review.food_image}" alt="Food" class="review-image">` : ''}
            </div>
        `;
    }

    static createFoodCard(food) {
        return `
            <div class="food-card fade-in" data-food-id="${food.id}">
                <img src="${food.image || 'https://via.placeholder.com/200x150?text=No+Image'}" 
                     alt="${food.name}" class="food-image">
                <div class="food-info">
                    <h3 class="food-name">${food.name}</h3>
                    <p class="food-description">${food.description || 'No description'}</p>
                    <div class="food-price">$${parseFloat(food.price).toFixed(2)}</div>
                    <div class="food-status">
                        <span class="availability ${food.is_available ? 'available' : 'unavailable'}">
                            ${food.is_available ? 'Available' : 'Unavailable'}
                        </span>
                        ${food.is_featured ? '<span class="featured">Featured</span>' : ''}
                    </div>
                    <div class="food-actions">
                        <button class="btn-edit" onclick="editFood('${food.id}')">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button class="btn-delete" onclick="deleteFood('${food.id}')">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </div>
            </div>
        `;
    }

    static createCustomerCard(customer) {
        return `
            <div class="customer-card fade-in" data-customer-id="${customer.id}">
                <div class="customer-avatar">
                    <img src="${customer.avatar || 'https://via.placeholder.com/60x60'}" alt="${customer.full_name}">
                </div>
                <div class="customer-info">
                    <h3 class="customer-name">${customer.full_name}</h3>
                    <p class="customer-email">${customer.email}</p>
                    <p class="customer-phone">${customer.phone || 'No phone'}</p>
                    <div class="customer-stats">
                        <span class="orders-count">${customer.total_orders || 0} orders</span>
                        <span class="last-order">${customer.last_order ? this.formatDate(customer.last_order) : 'No orders'}</span>
                    </div>
                </div>
            </div>
        `;
    }

    static createStatsCard(type, value, label, change) {
        const icons = {
            orders: 'fas fa-shopping-bag',
            delivered: 'fas fa-truck', 
            cancelled: 'fas fa-times-circle',
            revenue: 'fas fa-dollar-sign'
        };

        return `
            <div class="stat-card stat-${type} fade-in">
                <div class="stat-icon">
                    <i class="${icons[type]}"></i>
                </div>
                <div class="stat-content">
                    <h3>${value}</h3>
                    <p>${label}</p>
                    <span class="stat-change ${change >= 0 ? 'positive' : 'negative'}">
                        ${Math.abs(change)}% ${change >= 0 ? 'Up' : 'Down'} from yesterday
                    </span>
                </div>
            </div>
        `;
    }

    static createLoadingState(message = 'Loading...') {
        return `
            <div class="loading">
                <i class="fas fa-spinner fa-spin"></i>
                <span>${message}</span>
            </div>
        `;
    }

    static createEmptyState(icon, message) {
        return `
            <div class="empty-state">
                <i class="${icon}"></i>
                <p>${message}</p>
            </div>
        `;
    }

    static formatDate(dateString) {
        const date = new Date(dateString);
        const now = new Date();
        const diffTime = Math.abs(now - date);
        const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

        if (diffDays === 1) return 'Yesterday';
        if (diffDays <= 7) return `${diffDays} days ago`;
        
        return date.toLocaleDateString();
    }

    static formatCurrency(amount) {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD'
        }).format(amount);
    }

    static showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `
            <i class="fas fa-${type === 'success' ? 'check' : type === 'error' ? 'times' : 'info'}"></i>
            <span>${message}</span>
            <button onclick="this.parentElement.remove()">
                <i class="fas fa-times"></i>
            </button>
        `;

        document.body.appendChild(notification);

        setTimeout(() => {
            notification.remove();
        }, 5000);
    }

    static confirmDialog(message, onConfirm) {
        const modal = document.createElement('div');
        modal.className = 'modal-overlay';
        modal.innerHTML = `
            <div class="modal-content">
                <div class="modal-header">
                    <h3>Confirm Action</h3>
                </div>
                <div class="modal-body">
                    <p>${message}</p>
                </div>
                <div class="modal-footer">
                    <button class="btn-secondary" onclick="this.closest('.modal-overlay').remove()">
                        Cancel
                    </button>
                    <button class="btn-danger" onclick="confirmAction()">
                        Confirm
                    </button>
                </div>
            </div>
        `;

        modal.querySelector('.btn-danger').onclick = () => {
            onConfirm();
            modal.remove();
        };

        document.body.appendChild(modal);
    }

    static createSearchResults(results, type) {
        if (!results || results.length === 0) {
            return this.createEmptyState('fas fa-search', 'No results found');
        }

        const createCard = {
            restaurants: this.createRestaurantCard,
            foods: this.createFoodCard,
            orders: this.createOrderCard,
            customers: this.createCustomerCard
        };

        return results.map(item => createCard[type](item)).join('');
    }

    static initializeTooltips() {
        document.querySelectorAll('[data-tooltip]').forEach(element => {
            element.addEventListener('mouseenter', (e) => {
                const tooltip = document.createElement('div');
                tooltip.className = 'tooltip';
                tooltip.textContent = e.target.dataset.tooltip;
                document.body.appendChild(tooltip);

                const rect = e.target.getBoundingClientRect();
                tooltip.style.left = rect.left + 'px';
                tooltip.style.top = (rect.top - tooltip.offsetHeight - 5) + 'px';

                e.target._tooltip = tooltip;
            });

            element.addEventListener('mouseleave', (e) => {
                if (e.target._tooltip) {
                    e.target._tooltip.remove();
                    delete e.target._tooltip;
                }
            });
        });
    }

    static debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    static formatNumber(num) {
        if (num >= 1000000) {
            return (num / 1000000).toFixed(1) + 'M';
        }
        if (num >= 1000) {
            return (num / 1000).toFixed(1) + 'K';
        }
        return num.toString();
    }

    static calculatePercentageChange(current, previous) {
        if (previous === 0) return current > 0 ? 100 : 0;
        return ((current - previous) / previous) * 100;
    }

    static exportData(data, filename, format = 'csv') {
        let content = '';
        let mimeType = '';

        if (format === 'csv') {
            const headers = Object.keys(data[0]).join(',');
            const rows = data.map(row => Object.values(row).join(',')).join('\n');
            content = headers + '\n' + rows;
            mimeType = 'text/csv';
        } else if (format === 'json') {
            content = JSON.stringify(data, null, 2);
            mimeType = 'application/json';
        }

        const blob = new Blob([content], { type: mimeType });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${filename}.${format}`;
        a.click();
        window.URL.revokeObjectURL(url);
    }
}

// Export for module use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = DashboardComponents;
}