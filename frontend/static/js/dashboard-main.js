// Dashboard Main - dashboard-main.js

class DashboardManager {
    constructor() {
        this.currentRestaurant = null;
        this.currentSection = 'dashboard';
        this.accessToken = localStorage.getItem('accessToken');
        this.apiBaseUrl = '/api';
        this.searchTimeout = null;
        
        this.init();
    }

    init() {
        this.checkAuthentication();
        this.setupEventListeners();
        this.loadUserData();
        this.loadRestaurants();
        this.initializeCharts();
    }

    checkAuthentication() {
        if (!this.accessToken) {
            window.location.href = '/login/';
            return false;
        }
        return true;
    }

    setupEventListeners() {
        // Navigation
        document.querySelectorAll('.nav-item a').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const section = e.target.closest('a').dataset.section;
                this.navigateToSection(section);
            });
        });

        // Restaurant selector
        const restaurantSelect = document.getElementById('restaurant-select');
        if (restaurantSelect) {
            restaurantSelect.addEventListener('change', (e) => {
                this.selectRestaurant(e.target.value);
            });
        }

        // Global search
        const globalSearch = document.getElementById('global-search');
        if (globalSearch) {
            globalSearch.addEventListener('input', 
                DashboardComponents.debounce((e) => {
                    this.performGlobalSearch(e.target.value);
                }, 300)
            );
        }

        // Order status filter
        const orderStatusFilter = document.getElementById('order-status-filter');
        if (orderStatusFilter) {
            orderStatusFilter.addEventListener('change', (e) => {
                this.filterOrders(e.target.value);
            });
        }

        // Add food button
        const addFoodBtn = document.getElementById('add-food-btn');
        if (addFoodBtn) {
            addFoodBtn.addEventListener('click', () => {
                this.showAddFoodModal();
            });
        }

        // Period selector
        const periodSelect = document.querySelector('.period-select');
        if (periodSelect) {
            periodSelect.addEventListener('change', (e) => {
                this.updateChartsPeriod(e.target.value);
            });
        }
    }

    async fetchAPI(endpoint, options = {}) {
        const url = `${this.apiBaseUrl}${endpoint}`;
        const config = {
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${this.accessToken}`
            },
            ...options
        };

        try {
            const response = await fetch(url, config);
            
            if (response.status === 401) {
                localStorage.removeItem('accessToken');
                window.location.href = '/login/';
                return null;
            }

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            return response.status === 204 ? null : await response.json();
        } catch (error) {
            console.error('API Error:', error);
            DashboardComponents.showNotification(
                'An error occurred while fetching data', 
                'error'
            );
            return null;
        }
    }

    async loadUserData() {
        const userData = await this.fetchAPI('/users/profile/');
        if (userData) {
            this.updateUserInfo(userData);
        }
    }

    updateUserInfo(user) {
        const userName = document.querySelector('.user-profile span');
        const pageSubtitle = document.getElementById('page-subtitle');
        
        if (userName) {
            userName.textContent = `Hello, ${user.full_name}`;
        }
        
        if (pageSubtitle) {
            pageSubtitle.textContent = `Hi, ${user.full_name}. Welcome back to Sedap Admin!`;
        }
    }

    async loadRestaurants() {
        const restaurants = await this.fetchAPI('/restaurants/list/');
        if (restaurants && restaurants.results) {
            this.populateRestaurantSelector(restaurants.results);
            
            // Select first restaurant by default
            if (restaurants.results.length > 0) {
                this.selectRestaurant(restaurants.results[0].id);
            }
        }
    }

    populateRestaurantSelector(restaurants) {
        const select = document.getElementById('restaurant-select');
        if (!select) return;

        select.innerHTML = '<option value="">Select Restaurant...</option>';
        
        restaurants.forEach(restaurant => {
            const option = document.createElement('option');
            option.value = restaurant.id;
            option.textContent = restaurant.name;
            select.appendChild(option);
        });
    }

    async selectRestaurant(restaurantId) {
        if (!restaurantId) return;

        this.currentRestaurant = restaurantId;
        const select = document.getElementById('restaurant-select');
        if (select) {
            select.value = restaurantId;
        }

        // Load data for selected restaurant
        await this.loadDashboardData();
    }

    async loadDashboardData() {
        if (!this.currentRestaurant) return;

        // Load statistics
        const stats = await this.fetchAPI(`/restaurants/statistics/${this.currentRestaurant}/get/`);
        if (stats) {
            this.updateStatistics(stats);
        }

        // Load other data based on current section
        switch (this.currentSection) {
            case 'dashboard':
                await this.loadReviews();
                break;
            case 'orders':
                await this.loadOrders();
                break;
            case 'foods':
                await this.loadFoods();
                break;
            case 'customers':
                await this.loadCustomers();
                break;
        }
    }

    updateStatistics(stats) {
        // Update stat cards
        document.getElementById('total-orders').textContent = 
            DashboardComponents.formatNumber(stats.total_orders || 0);
        
        document.getElementById('total-delivered').textContent = 
            DashboardComponents.formatNumber(stats.orders_by_status?.DELIVERED || 0);
        
        document.getElementById('total-cancelled').textContent = 
            DashboardComponents.formatNumber(stats.orders_by_status?.CANCELLED || 0);
        
        document.getElementById('total-revenue').textContent = 
            DashboardComponents.formatCurrency(stats.total_revenue || 0);

        // Update charts with real data
        if (window.dashboardCharts) {
            window.dashboardCharts.updateStatsCharts({
                orderStats: {
                    total: stats.total_orders,
                    completed: stats.orders_by_status?.DELIVERED || 0
                },
                customerGrowth: {
                    percentage: stats.customer_growth_percentage || 22
                },
                revenueStats: {
                    target: stats.revenue_target || 10000,
                    achieved: stats.total_revenue || 0
                }
            });
        }
    }

    async loadOrders(status = '', page = 1) {
        if (!this.currentRestaurant) return;

        let endpoint = `/orders/?restaurant=${this.currentRestaurant}&page=${page}`;
        if (status) {
            endpoint += `&status=${status}`;
        }

        const orders = await this.fetchAPI(endpoint);
        if (orders) {
            this.displayOrders(orders.results || []);
        }
    }

    displayOrders(orders) {
        const container = document.getElementById('orders-list');
        if (!container) return;

        if (orders.length === 0) {
            container.innerHTML = DashboardComponents.createEmptyState(
                'fas fa-clipboard-list',
                'No orders found'
            );
            return;
        }

        container.innerHTML = orders
            .map(order => DashboardComponents.createOrderCard(order))
            .join('');
    }

    async loadRestaurantsList() {
        const restaurants = await this.fetchAPI('/restaurants/list/');
        if (restaurants) {
            this.displayRestaurants(restaurants.results || []);
        }
    }

    displayRestaurants(restaurants) {
        const container = document.getElementById('restaurants-list');
        if (!container) return;

        if (restaurants.length === 0) {
            container.innerHTML = DashboardComponents.createEmptyState(
                'fas fa-store',
                'No restaurants found'
            );
            return;
        }

        container.innerHTML = restaurants
            .map(restaurant => DashboardComponents.createRestaurantCard(restaurant))
            .join('');
    }

    async loadReviews() {
        if (!this.currentRestaurant) return;

        const reviews = await this.fetchAPI(`/restaurants/list/${this.currentRestaurant}/reviews/`);
        if (reviews) {
            this.displayReviews(reviews);
        }
    }

    displayReviews(reviews) {
        const container = document.getElementById('customer-reviews');
        if (!container) return;

        if (!reviews || reviews.length === 0) {
            container.innerHTML = DashboardComponents.createEmptyState(
                'fas fa-star',
                'No reviews yet'
            );
            return;
        }

        container.innerHTML = reviews
            .slice(0, 3) // Show only first 3 reviews
            .map(review => DashboardComponents.createReviewCard(review))
            .join('');
    }

    async loadFoods() {
        if (!this.currentRestaurant) return;

        const foods = await this.fetchAPI(`/menu-items/?restaurant=${this.currentRestaurant}`);
        if (foods) {
            this.displayFoods(foods.results || []);
        }
    }

    displayFoods(foods) {
        const container = document.getElementById('foods-list');
        if (!container) return;

        if (foods.length === 0) {
            container.innerHTML = DashboardComponents.createEmptyState(
                'fas fa-utensils',
                'No menu items found'
            );
            return;
        }

        container.innerHTML = foods
            .map(food => DashboardComponents.createFoodCard(food))
            .join('');
    }

    async loadCustomers() {
        // Load customers who have ordered from this restaurant
        if (!this.currentRestaurant) return;

        const orders = await this.fetchAPI(`/orders/?restaurant=${this.currentRestaurant}`);
        if (orders && orders.results) {
            const uniqueCustomers = this.extractUniqueCustomers(orders.results);
            this.displayCustomers(uniqueCustomers);
        }
    }

    extractUniqueCustomers(orders) {
        const customerMap = new Map();
        
        orders.forEach(order => {
            const customerId = order.customer;
            if (!customerMap.has(customerId)) {
                customerMap.set(customerId, {
                    id: customerId,
                    full_name: order.customer_name,
                    email: order.customer_email || 'N/A',
                    phone: order.customer_phone || 'N/A',
                    total_orders: 1,
                    last_order: order.created_at
                });
            } else {
                const customer = customerMap.get(customerId);
                customer.total_orders++;
                if (new Date(order.created_at) > new Date(customer.last_order)) {
                    customer.last_order = order.created_at;
                }
            }
        });

        return Array.from(customerMap.values());
    }

    displayCustomers(customers) {
        const container = document.getElementById('customers-list');
        if (!container) return;

        if (customers.length === 0) {
            container.innerHTML = DashboardComponents.createEmptyState(
                'fas fa-users',
                'No customers found'
            );
            return;
        }

        container.innerHTML = customers
            .map(customer => DashboardComponents.createCustomerCard(customer))
            .join('');
    }

    navigateToSection(section) {
        // Update navigation
        document.querySelectorAll('.nav-item').forEach(item => {
            item.classList.remove('active');
        });
        document.querySelector(`[data-section="${section}"]`).closest('.nav-item').classList.add('active');

        // Update content sections
        document.querySelectorAll('.content-section').forEach(section => {
            section.classList.remove('active');
        });
        document.getElementById(`${section}-section`).classList.add('active');

        // Update page title
        const titles = {
            dashboard: 'Dashboard',
            orders: 'Order Management',
            restaurants: 'My Restaurants',
            reviews: 'Customer Reviews',
            foods: 'Menu Management',
            customers: 'Customer Management'
        };

        document.getElementById('page-title').textContent = titles[section] || 'Dashboard';
        this.currentSection = section;

        // Load section-specific data
        switch (section) {
            case 'orders':
                this.loadOrders();
                break;
            case 'restaurants':
                this.loadRestaurantsList();
                break;
            case 'foods':
                this.loadFoods();
                break;
            case 'customers':
                this.loadCustomers();
                break;
            case 'reviews':
                this.loadReviews();
                break;
        }
    }

    async performGlobalSearch(query) {
        if (!query.trim()) return;

        const searchTypes = ['restaurants', 'foods', 'customers', 'orders'];
        const results = {};

        for (const type of searchTypes) {
            const endpoint = this.getSearchEndpoint(type, query);
            const data = await this.fetchAPI(endpoint);
            results[type] = data?.results || [];
        }

        this.displaySearchResults(results, query);
    }

    getSearchEndpoint(type, query) {
        const endpoints = {
            restaurants: `/restaurants/list/?search=${encodeURIComponent(query)}`,
            foods: `/menu-items/?search=${encodeURIComponent(query)}${this.currentRestaurant ? `&restaurant=${this.currentRestaurant}` : ''}`,
            customers: `/users/customers/?search=${encodeURIComponent(query)}`,
            orders: `/orders/?search=${encodeURIComponent(query)}${this.currentRestaurant ? `&restaurant=${this.currentRestaurant}` : ''}`
        };
        return endpoints[type];
    }

    displaySearchResults(results, query) {
        // Create search results modal or update current section
        console.log('Search results for:', query, results);
        // Implementation depends on UI design choice
    }

    filterOrders(status) {
        this.loadOrders(status);
    }

    async updateChartsPeriod(period) {
        // Update charts based on selected period
        if (!this.currentRestaurant) return;

        const chartData = await this.fetchAPI(
            `/restaurants/${this.currentRestaurant}/analytics/?period=${period}`
        );

        if (chartData && window.dashboardCharts) {
            window.dashboardCharts.updateOrderChart(chartData.weekly_orders);
            window.dashboardCharts.updateRevenueChart(chartData.monthly_revenue);
            window.dashboardCharts.updateOrdersCountChart(chartData.daily_orders);
        }
    }

    initializeCharts() {
        // Initialize charts after a short delay to ensure DOM is ready
        setTimeout(() => {
            if (window.dashboardCharts) {
                window.dashboardCharts.initializeAllCharts();
            }
        }, 100);
    }

    showAddFoodModal() {
        // Redirect to add food page or show modal
        window.location.href = '/my-restaurant/menu/items/add/';
    }

    // Action handlers for buttons
    editRestaurant(restaurantId) {
        window.location.href = `/my-restaurant/manage/`;
    }

    editFood(foodId) {
        window.location.href = `/my-restaurant/menu/items/${foodId}/edit/`;
    }

    async deleteFood(foodId) {
        DashboardComponents.confirmDialog(
            'Are you sure you want to delete this menu item?',
            async () => {
                const result = await this.fetchAPI(`/menu-items/${foodId}/`, {
                    method: 'DELETE'
                });

                if (result !== false) {
                    DashboardComponents.showNotification(
                        'Menu item deleted successfully',
                        'success'
                    );
                    this.loadFoods();
                }
            }
        );
    }

    // Export functionality
    exportReport(type) {
        const data = this.getCurrentSectionData();
        if (data) {
            DashboardComponents.exportData(data, `${type}_report_${Date.now()}`, 'csv');
        }
    }

    getCurrentSectionData() {
        // Return data based on current section
        switch (this.currentSection) {
            case 'orders':
                return this.extractOrdersData();
            case 'customers':
                return this.extractCustomersData();
            default:
                return null;
        }
    }

    extractOrdersData() {
        const orderCards = document.querySelectorAll('.order-card');
        return Array.from(orderCards).map(card => {
            const id = card.dataset.orderId;
            const customer = card.querySelector('.order-customer')?.textContent;
            const status = card.querySelector('.order-status')?.textContent;
            const total = card.querySelector('.order-details div:nth-child(2)')?.textContent;
            
            return { id, customer, status, total };
        });
    }

    extractCustomersData() {
        const customerCards = document.querySelectorAll('.customer-card');
        return Array.from(customerCards).map(card => {
            const name = card.querySelector('.customer-name')?.textContent;
            const email = card.querySelector('.customer-email')?.textContent;
            const orders = card.querySelector('.orders-count')?.textContent;
            
            return { name, email, orders };
        });
    }
}

// Global functions for button handlers
window.editRestaurant = function(restaurantId) {
    if (window.dashboardManager) {
        window.dashboardManager.editRestaurant(restaurantId);
    }
};

window.editFood = function(foodId) {
    if (window.dashboardManager) {
        window.dashboardManager.editFood(foodId);
    }
};

window.deleteFood = function(foodId) {
    if (window.dashboardManager) {
        window.dashboardManager.deleteFood(foodId);
    }
};

// Initialize dashboard when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    window.dashboardManager = new DashboardManager();
});

// Handle browser back/forward buttons
window.addEventListener('popstate', function(event) {
    if (event.state && event.state.section) {
        window.dashboardManager.navigateToSection(event.state.section);
    }
});

// Export for module use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = DashboardManager;
}