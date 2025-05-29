/**
 * Dashboard Manager Module - dashboard.js
 * Main controller for the restaurant dashboard
 */

class DashboardManager {
    constructor() {
        this.currentSection = 'dashboard';
        this.currentRestaurant = null;
        this.filters = {
            dateRange: 'month',
            status: '',
            search: ''
        };
        this.chartManager = null;
        this.orderManager = null;
        this.menuManager = null;
        
        this.init();
    }

    /**
     * Initialize dashboard
     */
    async init() {
        try {
            this.showLoading();
            
            // Check authentication
            if (!window.App.api.isAuthenticated()) {
                window.location.href = '/login/';
                return;
            }

            // Setup event listeners
            this.setupEventListeners();
            
            // Load initial data
            await this.loadInitialData();
            
            // Initialize managers
            this.initializeManagers();
            
            this.hideLoading();
            
            // Show dashboard section by default
            this.showSection('dashboard');
            
        } catch (error) {
            console.error('Dashboard initialization failed:', error);
            window.App.notifications.error('Failed to initialize dashboard');
            this.hideLoading();
        }
    }

    /**
     * Setup event listeners
     */
    setupEventListeners() {
        // Navigation links
        document.querySelectorAll('.nav-link').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const section = e.currentTarget.closest('.nav-item').dataset.section;
                this.showSection(section);
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
                Utils.debounce((e) => {
                    this.performGlobalSearch(e.target.value);
                }, 300)
            );
        }

        // User dropdown
        const userProfile = document.querySelector('.user-profile');
        if (userProfile) {
            userProfile.addEventListener('click', this.toggleUserDropdown.bind(this));
        }

        // Notifications
        const notificationsBtn = document.getElementById('notifications-btn');
        if (notificationsBtn) {
            notificationsBtn.addEventListener('click', this.toggleNotifications.bind(this));
        }

        // Restaurant status toggle
        const statusToggle = document.getElementById('restaurant-open-toggle');
        if (statusToggle) {
            statusToggle.addEventListener('change', this.toggleRestaurantStatus.bind(this));
        }

        // Click outside to close dropdowns
        document.addEventListener('click', this.handleOutsideClick.bind(this));

        // Keyboard shortcuts
        document.addEventListener('keydown', this.handleKeyboardShortcuts.bind(this));
    }

    /**
     * Load initial data
     */
    async loadInitialData() {
        try {
            // Load user profile
            const profile = await window.App.api.getProfile();
            this.updateUserInfo(profile);

            // Load restaurants
            const restaurants = await window.App.api.getRestaurants();
            this.populateRestaurantSelector(restaurants.results || []);

            // Auto-select first restaurant or user's restaurant
            if (restaurants.results && restaurants.results.length > 0) {
                const userRestaurant = restaurants.results.find(r => r.owner_name === profile.full_name);
                const selectedRestaurant = userRestaurant || restaurants.results[0];
                await this.selectRestaurant(selectedRestaurant.id);
            }

            // Load notifications
            await this.loadNotifications();

        } catch (error) {
            console.error('Failed to load initial data:', error);
            throw error;
        }
    }

    /**
     * Initialize sub-managers
     */
    initializeManagers() {
        // Initialize chart manager
        if (typeof ChartManager !== 'undefined') {
            this.chartManager = new ChartManager();
        }

        // Initialize order manager
        if (typeof OrderManager !== 'undefined') {
            this.orderManager = new OrderManager();
        }

        // Initialize menu manager
        if (typeof MenuManager !== 'undefined') {
            this.menuManager = new MenuManager();
        }
    }

    /**
     * Update user information in UI
     */
    updateUserInfo(user) {
        // Update header
        const profileName = document.querySelector('.profile-name');
        if (profileName) {
            profileName.textContent = user.full_name;
        }

        // Update sidebar
        const userName = document.querySelector('.user-name');
        if (userName) {
            userName.textContent = user.full_name;
        }

        // Update page subtitle
        const pageSubtitle = document.getElementById('page-subtitle');
        if (pageSubtitle) {
            pageSubtitle.textContent = `Welcome back! Here's what's happening with your restaurant.`;
        }
    }

    /**
     * Populate restaurant selector dropdown
     */
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

    /**
     * Select a restaurant and load its data
     */
    async selectRestaurant(restaurantId) {
        if (!restaurantId || restaurantId === this.currentRestaurant) return;

        try {
            this.showLoading('Loading restaurant data...');
            
            this.currentRestaurant = restaurantId;
            
            // Update selector
            const select = document.getElementById('restaurant-select');
            if (select) {
                select.value = restaurantId;
            }

            // Load restaurant data
            await this.loadRestaurantData();
            
            this.hideLoading();
            
        } catch (error) {
            console.error('Failed to select restaurant:', error);
            window.App.notifications.error('Failed to load restaurant data');
            this.hideLoading();
        }
    }

    /**
     * Load data for current restaurant
     */
    async loadRestaurantData() {
        if (!this.currentRestaurant) return;

        try {
            // Load restaurant stats
            const stats = await window.App.api.getRestaurantStats(this.currentRestaurant);
            this.updateStatistics(stats);

            // Load section-specific data
            switch (this.currentSection) {
                case 'dashboard':
                    await this.loadDashboardData();
                    break;
                case 'orders':
                    if (this.orderManager) {
                        await this.orderManager.loadOrders();
                    }
                    break;
                case 'menu':
                    if (this.menuManager) {
                        await this.menuManager.loadMenu();
                    }
                    break;
                case 'analytics':
                    await this.loadAnalyticsData();
                    break;
            }

        } catch (error) {
            console.error('Failed to load restaurant data:', error);
            throw error;
        }
    }

    /**
     * Load dashboard-specific data
     */
    async loadDashboardData() {
        try {
            // Load analytics data
            const analytics = await window.App.api.getDashboardAnalytics({
                restaurant_id: this.currentRestaurant,
                period: this.filters.dateRange
            });

            // Update charts
            if (this.chartManager) {
                this.chartManager.updateCharts(analytics);
            }

            // Load recent orders
            const orders = await window.App.api.getOrders({
                restaurant: this.currentRestaurant,
                page_size: 5
            });

            this.displayRecentOrders(orders.results || []);

        } catch (error) {
            console.error('Failed to load dashboard data:', error);
        }
    }

    /**
     * Update statistics cards
     */
    updateStatistics(stats) {
        // Update stat values
        const elements = {
            'total-orders': stats.total_orders || 0,
            'total-revenue': Utils.formatCurrency(stats.total_revenue || 0),
            'total-delivered': stats.orders_by_status?.DELIVERED || 0,
            'average-rating': (stats.average_rating || 0).toFixed(1),
            'total-customers': stats.total_customers || 0,
            'pending-orders': stats.orders_by_status?.PLACED || 0
        };

        Object.entries(elements).forEach(([id, value]) => {
            const element = document.getElementById(id);
            if (element) {
                element.textContent = value;
            }
        });

        // Update restaurant status
        this.updateRestaurantStatus(stats.is_open);
    }

    /**
     * Update restaurant status toggle
     */
    updateRestaurantStatus(isOpen) {
        const toggle = document.getElementById('restaurant-open-toggle');
        const statusText = document.getElementById('restaurant-status-text');
        
        if (toggle) {
            toggle.checked = isOpen;
        }
        
        if (statusText) {
            statusText.textContent = isOpen ? 'Open' : 'Closed';
            statusText.className = `status-text ${isOpen ? 'open' : 'closed'}`;
        }
    }

    /**
     * Toggle restaurant open/closed status
     */
    async toggleRestaurantStatus() {
        const toggle = document.getElementById('restaurant-open-toggle');
        if (!toggle || !this.currentRestaurant) return;

        try {
            const isOpen = toggle.checked;
            
            await window.App.api.updateRestaurant(this.currentRestaurant, {
                is_open: isOpen
            });
            
            this.updateRestaurantStatus(isOpen);
            
            window.App.notifications.success(
                `Restaurant ${isOpen ? 'opened' : 'closed'} successfully`
            );
            
        } catch (error) {
            // Revert toggle on error
            toggle.checked = !toggle.checked;
            console.error('Failed to update restaurant status:', error);
            window.App.notifications.error('Failed to update restaurant status');
        }
    }

    /**
     * Show a specific section
     */
    showSection(sectionName) {
        // Update navigation
        document.querySelectorAll('.nav-link').forEach(link => {
            link.classList.remove('active');
        });
        
        const activeNavItem = document.querySelector(`[data-section="${sectionName}"] .nav-link`);
        if (activeNavItem) {
            activeNavItem.classList.add('active');
        }

        // Update page title
        const titles = {
            dashboard: 'Dashboard',
            orders: 'Order Management',
            menu: 'Menu Management',
            analytics: 'Analytics',
            reviews: 'Customer Reviews',
            promotions: 'Promotions',
            restaurant: 'Restaurant Settings'
        };

        const pageTitle = document.getElementById('page-title');
        if (pageTitle) {
            pageTitle.textContent = titles[sectionName] || 'Dashboard';
        }

        // Hide all sections
        document.querySelectorAll('.content-section').forEach(section => {
            section.style.display = 'none';
        });

        // Show requested section
        const targetSection = document.getElementById(`${sectionName}-section`);
        if (targetSection) {
            targetSection.style.display = 'block';
        }

        this.currentSection = sectionName;

        // Load section-specific data
        this.loadSectionData(sectionName);
    }

    /**
     * Load data for specific section
     */
    async loadSectionData(sectionName) {
        if (!this.currentRestaurant) return;

        try {
            switch (sectionName) {
                case 'orders':
                    if (this.orderManager) {
                        await this.orderManager.loadOrders();
                    }
                    break;
                case 'menu':
                    if (this.menuManager) {
                        await this.menuManager.loadMenu();
                    }
                    break;
                case 'analytics':
                    await this.loadAnalyticsData();
                    break;
                case 'reviews':
                    await this.loadReviewsData();
                    break;
            }
        } catch (error) {
            console.error(`Failed to load ${sectionName} data:`, error);
        }
    }

    /**
     * Perform global search
     */
    async performGlobalSearch(query) {
        if (!query.trim() || query.length < 2) return;

        try {
            const results = await Promise.all([
                window.App.api.getOrders({ search: query, restaurant: this.currentRestaurant }),
                window.App.api.getMenuItems({ search: query, restaurant: this.currentRestaurant })
            ]);

            const [orders, menuItems] = results;
            this.displaySearchResults({
                orders: orders.results || [],
                menuItems: menuItems.results || []
            }, query);

        } catch (error) {
            console.error('Search failed:', error);
        }
    }

    /**
     * Display search results
     */
    displaySearchResults(results, query) {
        // Create and show search results modal or dropdown
        console.log('Search results for:', query, results);
        // Implementation depends on UI design
    }

    /**
     * Toggle user dropdown
     */
    toggleUserDropdown(e) {
        e.stopPropagation();
        const dropdown = document.getElementById('user-dropdown');
        if (dropdown) {
            dropdown.style.display = dropdown.style.display === 'none' ? 'block' : 'none';
        }
    }

    /**
     * Toggle notifications dropdown
     */
    toggleNotifications(e) {
        e.stopPropagation();
        const dropdown = document.getElementById('notifications-dropdown');
        if (dropdown) {
            dropdown.style.display = dropdown.style.display === 'none' ? 'block' : 'none';
        }
    }

    /**
     * Load notifications
     */
    async loadNotifications() {
        try {
            const notifications = await window.App.api.getNotifications({ page_size: 10 });
            this.displayNotifications(notifications.results || []);
            this.updateNotificationCount(notifications.results?.length || 0);
        } catch (error) {
            console.error('Failed to load notifications:', error);
        }
    }

    /**
     * Display notifications in dropdown
     */
    displayNotifications(notifications) {
        const container = document.getElementById('notifications-list');
        if (!container) return;

        if (notifications.length === 0) {
            container.innerHTML = '<div class="no-notifications">No new notifications</div>';
            return;
        }

        container.innerHTML = notifications.map(notification => `
            <div class="notification-item ${notification.read ? 'read' : 'unread'}" 
                 data-id="${notification.id}">
                <div class="notification-content">
                    <h5>${notification.title}</h5>
                    <p>${notification.message}</p>
                    <span class="notification-time">${Utils.formatTimeAgo(notification.created_at)}</span>
                </div>
                ${!notification.read ? '<div class="notification-dot"></div>' : ''}
            </div>
        `).join('');
    }

    /**
     * Update notification count badge
     */
    updateNotificationCount(count) {
        const badge = document.getElementById('notification-count');
        if (badge) {
            badge.textContent = count;
            badge.style.display = count > 0 ? 'flex' : 'none';
        }
    }

    /**
     * Handle clicks outside dropdowns
     */
    handleOutsideClick(e) {
        // Close user dropdown
        const userDropdown = document.getElementById('user-dropdown');
        const userProfile = document.querySelector('.user-profile');
        if (userDropdown && !userProfile?.contains(e.target)) {
            userDropdown.style.display = 'none';
        }

        // Close notifications dropdown
        const notificationsDropdown = document.getElementById('notifications-dropdown');
        const notificationsBtn = document.getElementById('notifications-btn');
        if (notificationsDropdown && !notificationsBtn?.contains(e.target)) {
            notificationsDropdown.style.display = 'none';
        }
    }

    /**
     * Handle keyboard shortcuts
     */
    handleKeyboardShortcuts(e) {
        // Alt + 1-6 for navigation
        if (e.altKey && e.key >= '1' && e.key <= '6') {
            e.preventDefault();
            const sections = ['dashboard', 'orders', 'menu', 'analytics', 'reviews', 'restaurant'];
            const index = parseInt(e.key) - 1;
            if (sections[index]) {
                this.showSection(sections[index]);
            }
        }

        // Escape to close modals/dropdowns
        if (e.key === 'Escape') {
            document.querySelectorAll('.modal-overlay').forEach(modal => {
                modal.style.display = 'none';
            });
            
            document.getElementById('user-dropdown').style.display = 'none';
            document.getElementById('notifications-dropdown').style.display = 'none';
        }
    }

    /**
     * Show loading overlay
     */
    showLoading(message = 'Loading...') {
        const overlay = document.getElementById('loading-overlay');
        if (overlay) {
            const messageEl = overlay.querySelector('p');
            if (messageEl) {
                messageEl.textContent = message;
            }
            overlay.style.display = 'flex';
        }
    }

    /**
     * Hide loading overlay
     */
    hideLoading() {
        const overlay = document.getElementById('loading-overlay');
        if (overlay) {
            overlay.style.display = 'none';
        }
    }

    /**
     * Display recent orders on dashboard
     */
    displayRecentOrders(orders) {
        const container = document.getElementById('recent-orders-list');
        if (!container) return;

        if (orders.length === 0) {
            container.innerHTML = '<div class="empty-state">No recent orders</div>';
            return;
        }

        container.innerHTML = orders.map(order => `
            <div class="order-item" onclick="viewOrderDetails('${order.id}')">
                <div class="order-info">
                    <h5>Order #${order.id.slice(-8)}</h5>
                    <p>${order.customer_name}</p>
                </div>
                <div class="order-status">
                    <span class="status-badge ${order.status.toLowerCase()}">${order.status}</span>
                </div>
                <div class="order-total">
                    ${Utils.formatCurrency(order.total_price)}
                </div>
            </div>
        `).join('');
    }

    /**
     * Refresh current section data
     */
    async refresh() {
        try {
            this.showLoading('Refreshing...');
            await this.loadRestaurantData();
            window.App.notifications.success('Data refreshed successfully');
        } catch (error) {
            console.error('Refresh failed:', error);
            window.App.notifications.error('Failed to refresh data');
        } finally {
            this.hideLoading();
        }
    }

    /**
     * Logout user
     */
    async logout() {
        try {
            // Clear tokens
            window.App.api.clearTokens();
            
            // Redirect to login
            window.location.href = '/login/';
            
        } catch (error) {
            console.error('Logout failed:', error);
            // Force redirect anyway
            window.location.href = '/login/';
        }
    }
}

// Global functions for HTML onclick handlers
window.showUserMenu = function() {
    if (window.dashboardManager) {
        window.dashboardManager.toggleUserDropdown(new Event('click'));
    }
};

window.showSettings = function() {
    console.log('Show settings modal');
};

window.showUserDropdown = function() {
    if (window.dashboardManager) {
        window.dashboardManager.toggleUserDropdown(new Event('click'));
    }
};

window.logout = function() {
    if (window.dashboardManager) {
        window.dashboardManager.logout();
    }
};

window.markAllNotificationsRead = function() {
    if (window.App.api) {
        window.App.api.markAllNotificationsRead();
    }
};

window.viewOrderDetails = function(orderId) {
    if (window.dashboardManager && window.dashboardManager.orderManager) {
        window.dashboardManager.orderManager.showOrderDetails(orderId);
    }
};

// Export for module use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = DashboardManager;
}
