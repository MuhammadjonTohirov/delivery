/**
 * Notification Manager
 * Handles displaying toast notifications, alerts, and messages
 */

class NotificationManager {
    constructor() {
        this.container = null;
        this.notifications = new Map();
        this.defaultDuration = 5000;
        this.maxNotifications = 5;
        this.init();
    }

    init() {
        this.createContainer();
        this.setupStyles();
    }

    createContainer() {
        // Find existing container or create new one
        this.container = document.getElementById('notifications-container');
        
        if (!this.container) {
            this.container = document.createElement('div');
            this.container.id = 'notifications-container';
            this.container.className = 'notification-container';
            document.body.appendChild(this.container);
        }
    }

    setupStyles() {
        // Add dynamic styles if needed
        if (!document.querySelector('#notification-styles')) {
            const style = document.createElement('style');
            style.id = 'notification-styles';
            style.textContent = `
                .tooltip {
                    position: absolute;
                    background: #1f2937;
                    color: white;
                    padding: 0.5rem 0.75rem;
                    border-radius: 0.375rem;
                    font-size: 0.875rem;
                    z-index: 1200;
                    opacity: 0;
                    transform: translateY(-4px);
                    transition: all 0.2s;
                    pointer-events: none;
                    white-space: nowrap;
                }
                .tooltip.show {
                    opacity: 1;
                    transform: translateY(0);
                }
                .tooltip::before {
                    content: '';
                    position: absolute;
                    width: 0;
                    height: 0;
                    border: 4px solid transparent;
                }
                .tooltip-top::before {
                    bottom: -8px;
                    left: 50%;
                    transform: translateX(-50%);
                    border-top-color: #1f2937;
                }
                .tooltip-bottom::before {
                    top: -8px;
                    left: 50%;
                    transform: translateX(-50%);
                    border-bottom-color: #1f2937;
                }
                .tooltip-left::before {
                    right: -8px;
                    top: 50%;
                    transform: translateY(-50%);
                    border-left-color: #1f2937;
                }
                .tooltip-right::before {
                    left: -8px;
                    top: 50%;
                    transform: translateY(-50%);
                    border-right-color: #1f2937;
                }
            `;
            document.head.appendChild(style);
        }
    }

    /**
     * Show a success notification
     * @param {string} message - The notification message
     * @param {object} options - Additional options
     */
    success(message, options = {}) {
        return this.show(message, { ...options, type: 'success' });
    }

    /**
     * Show an error notification
     * @param {string} message - The notification message
     * @param {object} options - Additional options
     */
    error(message, options = {}) {
        return this.show(message, { 
            ...options, 
            type: 'error', 
            duration: options.duration || 8000 // Errors stay longer
        });
    }

    /**
     * Show a warning notification
     * @param {string} message - The notification message
     * @param {object} options - Additional options
     */
    warning(message, options = {}) {
        return this.show(message, { ...options, type: 'warning' });
    }

    /**
     * Show an info notification
     * @param {string} message - The notification message
     * @param {object} options - Additional options
     */
    info(message, options = {}) {
        return this.show(message, { ...options, type: 'info' });
    }

    /**
     * Show a loading notification
     * @param {string} message - The notification message
     * @param {object} options - Additional options
     */
    loading(message, options = {}) {
        return this.show(message, { 
            ...options, 
            type: 'loading', 
            duration: 0, // Don't auto-dismiss
            closable: false
        });
    }

    /**
     * Show a notification
     * @param {string} message - The notification message
     * @param {object} options - Notification options
     */
    show(message, options = {}) {
        const config = {
            type: 'info',
            title: '',
            duration: this.defaultDuration,
            closable: true,
            actions: [],
            image: null,
            compact: false,
            ...options
        };

        // Limit number of notifications
        if (this.notifications.size >= this.maxNotifications) {
            const oldestId = this.notifications.keys().next().value;
            this.dismiss(oldestId);
        }

        const notification = this.createNotification(message, config);
        const id = this.generateId();
        
        this.notifications.set(id, notification);
        notification.dataset.notificationId = id;
        
        this.container.appendChild(notification);
        
        // Show notification with animation
        requestAnimationFrame(() => {
            notification.classList.add('show');
        });

        // Auto-dismiss if duration is set
        if (config.duration > 0) {
            this.scheduleAutoDismiss(id, config.duration);
        }

        return id;
    }

    /**
     * Create notification element
     * @param {string} message - The notification message
     * @param {object} config - Notification configuration
     */
    createNotification(message, config) {
        const notification = document.createElement('div');
        notification.className = `notification ${config.type}`;
        
        if (config.compact) {
            notification.classList.add('compact');
        }

        if (config.image) {
            notification.classList.add('with-image');
        }

        // Create notification content
        let content = '';

        // Icon
        if (!config.image) {
            content += `<div class="notification-icon">
                <i class="fas ${this.getIcon(config.type)}"></i>
            </div>`;
        } else {
            content += `<img src="${config.image}" alt="" class="notification-image">`;
        }

        // Content
        content += `<div class="notification-content">`;
        
        if (config.title) {
            content += `<h4 class="notification-title">${config.title}</h4>`;
        }
        
        content += `<p class="notification-message">${message}</p>`;

        // Actions
        if (config.actions && config.actions.length > 0) {
            content += `<div class="notification-actions">`;
            config.actions.forEach(action => {
                content += `<button class="notification-action ${action.type || ''}" 
                    onclick="${action.onclick || ''}">${action.text}</button>`;
            });
            content += `</div>`;
        }

        content += `</div>`;

        // Close button
        if (config.closable) {
            content += `<button class="notification-close" aria-label="Close">
                <i class="fas fa-times"></i>
            </button>`;
        }

        // Progress bar for auto-dismiss
        if (config.duration > 0) {
            notification.dataset.autoDismiss = 'true';
            notification.style.setProperty('--duration', config.duration + 'ms');
            content += `<div class="notification-progress">
                <div class="notification-progress-bar"></div>
            </div>`;
        }

        notification.innerHTML = content;

        // Add event listeners
        this.addNotificationListeners(notification);

        return notification;
    }

    /**
     * Add event listeners to notification
     * @param {HTMLElement} notification - The notification element
     */
    addNotificationListeners(notification) {
        // Close button
        const closeButton = notification.querySelector('.notification-close');
        if (closeButton) {
            closeButton.addEventListener('click', (e) => {
                e.stopPropagation();
                const id = notification.dataset.notificationId;
                this.dismiss(id);
            });
        }

        // Click to dismiss (optional)
        notification.addEventListener('click', () => {
            if (notification.dataset.clickToDismiss === 'true') {
                const id = notification.dataset.notificationId;
                this.dismiss(id);
            }
        });

        // Pause auto-dismiss on hover
        notification.addEventListener('mouseenter', () => {
            const id = notification.dataset.notificationId;
            this.pauseAutoDismiss(id);
        });

        notification.addEventListener('mouseleave', () => {
            const id = notification.dataset.notificationId;
            this.resumeAutoDismiss(id);
        });
    }

    /**
     * Dismiss a notification
     * @param {string} id - The notification ID
     */
    dismiss(id) {
        const notification = this.notifications.get(id);
        if (!notification) return;

        // Clear any pending auto-dismiss
        if (notification._autoDismissTimeout) {
            clearTimeout(notification._autoDismissTimeout);
        }

        // Hide with animation
        notification.classList.add('hide');
        
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
            this.notifications.delete(id);
        }, 300);
    }

    /**
     * Dismiss all notifications
     */
    dismissAll() {
        this.notifications.forEach((notification, id) => {
            this.dismiss(id);
        });
    }

    /**
     * Update an existing notification
     * @param {string} id - The notification ID
     * @param {string} message - New message
     * @param {object} options - New options
     */
    update(id, message, options = {}) {
        const notification = this.notifications.get(id);
        if (!notification) return;

        const messageElement = notification.querySelector('.notification-message');
        if (messageElement) {
            messageElement.textContent = message;
        }

        const titleElement = notification.querySelector('.notification-title');
        if (options.title && titleElement) {
            titleElement.textContent = options.title;
        }

        // Update type if changed
        if (options.type) {
            notification.className = `notification ${options.type} show`;
            const icon = notification.querySelector('.notification-icon i');
            if (icon) {
                icon.className = `fas ${this.getIcon(options.type)}`;
            }
        }
    }

    /**
     * Schedule auto-dismiss for a notification
     * @param {string} id - The notification ID
     * @param {number} duration - Duration in milliseconds
     */
    scheduleAutoDismiss(id, duration) {
        const notification = this.notifications.get(id);
        if (!notification) return;

        notification._autoDismissTimeout = setTimeout(() => {
            this.dismiss(id);
        }, duration);
    }

    /**
     * Pause auto-dismiss for a notification
     * @param {string} id - The notification ID
     */
    pauseAutoDismiss(id) {
        const notification = this.notifications.get(id);
        if (!notification || !notification._autoDismissTimeout) return;

        clearTimeout(notification._autoDismissTimeout);
        notification._autoDismissTimeout = null;
        
        // Pause CSS animation
        const progressBar = notification.querySelector('.notification-progress-bar');
        if (progressBar) {
            progressBar.style.animationPlayState = 'paused';
        }
    }

    /**
     * Resume auto-dismiss for a notification
     * @param {string} id - The notification ID
     */
    resumeAutoDismiss(id) {
        const notification = this.notifications.get(id);
        if (!notification) return;

        // Resume CSS animation
        const progressBar = notification.querySelector('.notification-progress-bar');
        if (progressBar) {
            progressBar.style.animationPlayState = 'running';
        }

        // Calculate remaining time and schedule dismiss
        // This is a simplified approach - in practice, you'd want to track elapsed time
        const duration = parseInt(notification.style.getPropertyValue('--duration'));
        if (duration) {
            this.scheduleAutoDismiss(id, duration / 2); // Rough estimate
        }
    }

    /**
     * Get icon for notification type
     * @param {string} type - The notification type
     */
    getIcon(type) {
        const icons = {
            success: 'fa-check',
            error: 'fa-times',
            warning: 'fa-exclamation',
            info: 'fa-info',
            loading: 'fa-spinner'
        };
        return icons[type] || icons.info;
    }

    /**
     * Generate unique ID for notification
     */
    generateId() {
        return 'notification-' + Date.now() + '-' + Math.random().toString(36).substr(2, 9);
    }

    /**
     * Show a confirmation notification with Yes/No buttons
     * @param {string} message - The confirmation message
     * @param {object} options - Additional options
     */
    confirm(message, options = {}) {
        return new Promise((resolve) => {
            const config = {
                title: options.title || 'Confirm',
                type: 'warning',
                closable: false,
                duration: 0,
                actions: [
                    {
                        text: options.cancelText || 'Cancel',
                        type: 'secondary',
                        onclick: () => {
                            this.dismiss(id);
                            resolve(false);
                        }
                    },
                    {
                        text: options.confirmText || 'Confirm',
                        type: 'primary',
                        onclick: () => {
                            this.dismiss(id);
                            resolve(true);
                        }
                    }
                ],
                ...options
            };

            const id = this.show(message, config);
        });
    }

    /**
     * Show a prompt notification with input field
     * @param {string} message - The prompt message
     * @param {object} options - Additional options
     */
    prompt(message, options = {}) {
        return new Promise((resolve) => {
            const inputId = 'prompt-input-' + Date.now();
            const enhancedMessage = `
                ${message}
                <div style="margin-top: 1rem;">
                    <input type="text" id="${inputId}" class="form-input" 
                           placeholder="${options.placeholder || ''}" 
                           value="${options.defaultValue || ''}" 
                           style="width: 100%; padding: 0.5rem; border: 1px solid #d1d5db; border-radius: 0.375rem;">
                </div>
            `;

            const config = {
                title: options.title || 'Input Required',
                type: 'info',
                closable: false,
                duration: 0,
                actions: [
                    {
                        text: options.cancelText || 'Cancel',
                        type: 'secondary',
                        onclick: () => {
                            this.dismiss(id);
                            resolve(null);
                        }
                    },
                    {
                        text: options.confirmText || 'OK',
                        type: 'primary',
                        onclick: () => {
                            const input = document.getElementById(inputId);
                            const value = input ? input.value : '';
                            this.dismiss(id);
                            resolve(value);
                        }
                    }
                ],
                ...options
            };

            const id = this.show(enhancedMessage, config);
            
            // Focus input after notification is shown
            setTimeout(() => {
                const input = document.getElementById(inputId);
                if (input) {
                    input.focus();
                    input.addEventListener('keydown', (e) => {
                        if (e.key === 'Enter') {
                            const value = input.value;
                            this.dismiss(id);
                            resolve(value);
                        } else if (e.key === 'Escape') {
                            this.dismiss(id);
                            resolve(null);
                        }
                    });
                }
            }, 100);
        });
    }

    /**
     * Clear all notifications
     */
    clear() {
        this.dismissAll();
    }

    /**
     * Get notification count
     */
    getCount() {
        return this.notifications.size;
    }

    /**
     * Check if notifications are supported
     */
    isSupported() {
        return typeof document !== 'undefined';
    }
}

// Initialize notification manager
window.NotificationManager = NotificationManager;
