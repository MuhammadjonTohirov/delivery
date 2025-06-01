/**
 * Components Manager
 * Handles reusable UI components and interactions
 */

class ComponentsManager {
    constructor() {
        this.components = new Map();
        this.init();
    }

    init() {
        this.initDropdowns();
        this.initTabs();
        this.initAccordions();
        this.initTooltips();
        this.initLoadingStates();
    }

    // Dropdown Component
    initDropdowns() {
        document.addEventListener('click', (e) => {
            const dropdown = e.target.closest('.dropdown');
            const dropdownButton = e.target.closest('.dropdown-button, .chart-dropdown-button');
            
            if (dropdownButton && dropdown) {
                e.preventDefault();
                e.stopPropagation();
                this.toggleDropdown(dropdown);
            } else {
                // Close all dropdowns when clicking outside
                this.closeAllDropdowns();
            }
        });

        // Close dropdowns on escape key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.closeAllDropdowns();
            }
        });
    }

    toggleDropdown(dropdown) {
        const isActive = dropdown.classList.contains('active');
        
        // Close all other dropdowns
        this.closeAllDropdowns();
        
        // Toggle current dropdown
        if (!isActive) {
            dropdown.classList.add('active');
        }
    }

    closeAllDropdowns() {
        document.querySelectorAll('.dropdown, .chart-dropdown').forEach(dropdown => {
            dropdown.classList.remove('active');
        });
    }

    // Tabs Component
    initTabs() {
        document.addEventListener('click', (e) => {
            const tabButton = e.target.closest('[data-tab-target]');
            if (!tabButton) return;

            e.preventDefault();
            const target = tabButton.dataset.tabTarget;
            const tabGroup = tabButton.closest('[data-tab-group]');
            
            if (tabGroup) {
                this.switchTab(tabGroup, target);
            }
        });
    }

    switchTab(tabGroup, targetId) {
        // Remove active class from all tab buttons in group
        tabGroup.querySelectorAll('[data-tab-target]').forEach(btn => {
            btn.classList.remove('active');
        });

        // Remove active class from all tab contents in group
        tabGroup.querySelectorAll('[data-tab-content]').forEach(content => {
            content.classList.remove('active');
        });

        // Add active class to clicked button
        const activeButton = tabGroup.querySelector(`[data-tab-target="${targetId}"]`);
        if (activeButton) {
            activeButton.classList.add('active');
        }

        // Show target content
        const targetContent = document.getElementById(targetId);
        if (targetContent) {
            targetContent.classList.add('active');
        }
    }

    // Accordion Component
    initAccordions() {
        document.addEventListener('click', (e) => {
            const accordionButton = e.target.closest('.accordion-button');
            if (!accordionButton) return;

            e.preventDefault();
            const accordionItem = accordionButton.closest('.accordion-item');
            const accordionContent = accordionItem?.querySelector('.accordion-content');
            
            if (accordionItem && accordionContent) {
                this.toggleAccordion(accordionItem, accordionContent);
            }
        });
    }

    toggleAccordion(item, content) {
        const isOpen = item.classList.contains('active');
        
        if (isOpen) {
            item.classList.remove('active');
            content.style.maxHeight = null;
        } else {
            item.classList.add('active');
            content.style.maxHeight = content.scrollHeight + 'px';
        }
    }

    // Tooltips Component
    initTooltips() {
        const tooltipElements = document.querySelectorAll('[data-tooltip]');
        
        tooltipElements.forEach(element => {
            element.addEventListener('mouseenter', (e) => {
                this.showTooltip(e.target);
            });
            
            element.addEventListener('mouseleave', (e) => {
                this.hideTooltip(e.target);
            });
        });
    }

    showTooltip(element) {
        const text = element.dataset.tooltip;
        const position = element.dataset.tooltipPosition || 'top';
        
        if (!text) return;

        // Remove existing tooltip
        this.hideTooltip(element);

        // Create tooltip
        const tooltip = document.createElement('div');
        tooltip.className = `tooltip tooltip-${position}`;
        tooltip.textContent = text;
        tooltip.id = 'tooltip-' + Date.now();
        
        document.body.appendChild(tooltip);
        
        // Position tooltip
        this.positionTooltip(element, tooltip, position);
        
        // Store tooltip reference
        element._tooltip = tooltip;
        
        // Show tooltip
        requestAnimationFrame(() => {
            tooltip.classList.add('show');
        });
    }

    hideTooltip(element) {
        if (element._tooltip) {
            element._tooltip.remove();
            element._tooltip = null;
        }
    }

    positionTooltip(element, tooltip, position) {
        const rect = element.getBoundingClientRect();
        const tooltipRect = tooltip.getBoundingClientRect();
        
        let left, top;
        
        switch (position) {
            case 'top':
                left = rect.left + (rect.width / 2) - (tooltipRect.width / 2);
                top = rect.top - tooltipRect.height - 8;
                break;
            case 'bottom':
                left = rect.left + (rect.width / 2) - (tooltipRect.width / 2);
                top = rect.bottom + 8;
                break;
            case 'left':
                left = rect.left - tooltipRect.width - 8;
                top = rect.top + (rect.height / 2) - (tooltipRect.height / 2);
                break;
            case 'right':
                left = rect.right + 8;
                top = rect.top + (rect.height / 2) - (tooltipRect.height / 2);
                break;
            default:
                left = rect.left + (rect.width / 2) - (tooltipRect.width / 2);
                top = rect.top - tooltipRect.height - 8;
        }
        
        tooltip.style.left = Math.max(8, left) + 'px';
        tooltip.style.top = Math.max(8, top) + 'px';
    }

    // Loading States
    initLoadingStates() {
        // This will be used by other components to show loading states
    }

    showLoadingSpinner(element, text = 'Loading...') {
        if (!element) return;

        const spinner = document.createElement('div');
        spinner.className = 'loading-spinner';
        spinner.innerHTML = `
            <i class="fas fa-spinner fa-spin"></i>
            <span class="loading-text">${text}</span>
        `;
        
        element.innerHTML = '';
        element.appendChild(spinner);
        element.classList.add('loading');
    }

    hideLoadingSpinner(element) {
        if (!element) return;
        
        element.classList.remove('loading');
        const spinner = element.querySelector('.loading-spinner');
        if (spinner) {
            spinner.remove();
        }
    }

    // Button States
    setButtonLoading(button, text = '') {
        if (!button) return;
        
        const originalText = button.textContent;
        button.dataset.originalText = originalText;
        button.disabled = true;
        button.classList.add('loading');
        
        button.innerHTML = `
            <i class="fas fa-spinner fa-spin"></i>
            ${text || 'Loading...'}
        `;
    }

    setButtonNormal(button) {
        if (!button) return;
        
        button.disabled = false;
        button.classList.remove('loading');
        
        const originalText = button.dataset.originalText || 'Submit';
        button.textContent = originalText;
    }

    // Form Validation Helper
    validateForm(form) {
        if (!form) return false;
        
        let isValid = true;
        const requiredFields = form.querySelectorAll('[required]');
        
        requiredFields.forEach(field => {
            const value = field.value.trim();
            const fieldGroup = field.closest('.form-group');
            
            // Remove previous error states
            field.classList.remove('error');
            if (fieldGroup) {
                const errorMsg = fieldGroup.querySelector('.error-message');
                if (errorMsg) errorMsg.remove();
            }
            
            // Validate field
            if (!value) {
                isValid = false;
                field.classList.add('error');
                
                if (fieldGroup) {
                    const errorDiv = document.createElement('div');
                    errorDiv.className = 'error-message';
                    errorDiv.textContent = `${field.placeholder || 'This field'} is required`;
                    fieldGroup.appendChild(errorDiv);
                }
            }
        });
        
        return isValid;
    }

    // Confirmation Dialog
    showConfirmDialog(options = {}) {
        const {
            title = 'Confirm Action',
            message = 'Are you sure you want to continue?',
            confirmText = 'Confirm',
            cancelText = 'Cancel',
            type = 'warning'
        } = options;

        return new Promise((resolve) => {
            const modal = document.createElement('div');
            modal.className = 'modal-overlay confirmation-modal';
            modal.innerHTML = `
                <div class="modal modal-sm">
                    <div class="modal-header">
                        <h3 class="modal-title">${title}</h3>
                    </div>
                    <div class="modal-body">
                        <div class="confirmation-icon ${type}">
                            <i class="fas ${this.getConfirmationIcon(type)}"></i>
                        </div>
                        <h4 class="confirmation-title">${title}</h4>
                        <p class="confirmation-message">${message}</p>
                    </div>
                    <div class="modal-footer">
                        <button class="btn btn-secondary cancel-btn">${cancelText}</button>
                        <button class="btn btn-${type === 'danger' ? 'danger' : 'primary'} confirm-btn">${confirmText}</button>
                    </div>
                </div>
            `;

            document.body.appendChild(modal);

            // Show modal
            requestAnimationFrame(() => {
                modal.classList.add('active');
            });

            // Event listeners
            const confirmBtn = modal.querySelector('.confirm-btn');
            const cancelBtn = modal.querySelector('.cancel-btn');

            const cleanup = () => {
                modal.classList.remove('active');
                setTimeout(() => modal.remove(), 300);
            };

            confirmBtn.addEventListener('click', () => {
                cleanup();
                resolve(true);
            });

            cancelBtn.addEventListener('click', () => {
                cleanup();
                resolve(false);
            });

            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    cleanup();
                    resolve(false);
                }
            });
        });
    }

    getConfirmationIcon(type) {
        switch (type) {
            case 'danger': return 'fa-exclamation-triangle';
            case 'success': return 'fa-check-circle';
            case 'info': return 'fa-info-circle';
            default: return 'fa-question-circle';
        }
    }

    // Utility: Debounce function
    debounce(func, wait) {
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

    // Utility: Format currency
    formatCurrency(amount, currency = 'USD') {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: currency
        }).format(amount);
    }

    // Utility: Format date
    formatDate(date, options = {}) {
        const defaultOptions = {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        };
        
        return new Intl.DateTimeFormat('en-US', { ...defaultOptions, ...options }).format(new Date(date));
    }

    // Utility: Copy to clipboard
    async copyToClipboard(text) {
        try {
            await navigator.clipboard.writeText(text);
            if (window.App?.notifications) {
                window.App.notifications.success('Copied to clipboard');
            }
            return true;
        } catch (err) {
            console.error('Failed to copy: ', err);
            if (window.App?.notifications) {
                window.App.notifications.error('Failed to copy to clipboard');
            }
            return false;
        }
    }
}

// Initialize components manager
window.ComponentsManager = ComponentsManager;
