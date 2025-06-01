/**
 * Modal Manager
 * Handles modal dialogs, popups, and overlays
 */

class ModalManager {
    constructor() {
        this.modals = new Map();
        this.modalStack = [];
        this.backdropClickClose = true;
        this.escapeKeyClose = true;
        this.init();
    }

    init() {
        this.createContainer();
        this.setupEventListeners();
    }

    createContainer() {
        // Find existing container or create new one
        this.container = document.getElementById('modals-container');
        
        if (!this.container) {
            this.container = document.createElement('div');
            this.container.id = 'modals-container';
            document.body.appendChild(this.container);
        }
    }

    setupEventListeners() {
        // Handle escape key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.escapeKeyClose && this.modalStack.length > 0) {
                const topModalId = this.modalStack[this.modalStack.length - 1];
                this.close(topModalId);
            }
        });

        // Handle backdrop clicks
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('modal-overlay') && this.backdropClickClose) {
                const modalId = e.target.dataset.modalId;
                if (modalId) {
                    this.close(modalId);
                }
            }
        });

        // Handle close button clicks
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('modal-close') || e.target.closest('.modal-close')) {
                const modal = e.target.closest('.modal-overlay');
                if (modal && modal.dataset.modalId) {
                    this.close(modal.dataset.modalId);
                }
            }
        });
    }

    /**
     * Show a modal
     * @param {object} options - Modal configuration
     */
    show(options = {}) {
        const config = {
            title: '',
            content: '',
            size: 'md', // sm, md, lg, xl, fullscreen
            closable: true,
            backdrop: true,
            escapeClose: true,
            className: '',
            buttons: [],
            onShow: null,
            onHide: null,
            ...options
        };

        const modalId = this.generateId();
        const modal = this.createModal(modalId, config);
        
        this.modals.set(modalId, { element: modal, config });
        this.container.appendChild(modal);
        
        // Add to stack
        this.modalStack.push(modalId);
        
        // Show modal with animation
        requestAnimationFrame(() => {
            modal.classList.add('active');
            if (config.onShow) {
                config.onShow(modalId, modal);
            }
        });

        // Manage body scroll
        this.updateBodyScroll();

        return modalId;
    }

    /**
     * Create modal element
     * @param {string} modalId - Unique modal ID
     * @param {object} config - Modal configuration
     */
    createModal(modalId, config) {
        const overlay = document.createElement('div');
        overlay.className = `modal-overlay ${config.className}`;
        overlay.dataset.modalId = modalId;
        
        if (!config.backdrop) {
            overlay.dataset.backdrop = 'static';
        }

        const modal = document.createElement('div');
        modal.className = `modal modal-${config.size}`;
        
        let content = '';

        // Header
        if (config.title || config.closable) {
            content += `<div class="modal-header">`;
            if (config.title) {
                content += `<h3 class="modal-title">${config.title}</h3>`;
            }
            if (config.closable) {
                content += `<button class="modal-close" aria-label="Close">
                    <i class="fas fa-times"></i>
                </button>`;
            }
            content += `</div>`;
        }

        // Body
        content += `<div class="modal-body">
            ${config.content}
        </div>`;

        // Footer with buttons
        if (config.buttons && config.buttons.length > 0) {
            content += `<div class="modal-footer">`;
            config.buttons.forEach(button => {
                const buttonClass = `btn ${button.class || 'btn-secondary'}`;
                content += `<button class="${buttonClass}" data-action="${button.action || ''}" 
                    ${button.dismiss ? 'data-dismiss="modal"' : ''}>
                    ${button.text}
                </button>`;
            });
            content += `</div>`;
        }

        modal.innerHTML = content;
        overlay.appendChild(modal);

        // Add button event listeners
        this.addButtonListeners(overlay, modalId);

        return overlay;
    }

    /**
     * Add event listeners to modal buttons
     * @param {HTMLElement} modal - Modal element
     * @param {string} modalId - Modal ID
     */
    addButtonListeners(modal, modalId) {
        const buttons = modal.querySelectorAll('[data-action], [data-dismiss]');
        
        buttons.forEach(button => {
            button.addEventListener('click', (e) => {
                const action = button.dataset.action;
                const dismiss = button.dataset.dismiss;
                
                if (dismiss === 'modal') {
                    this.close(modalId);
                }
                
                if (action) {
                    const modalData = this.modals.get(modalId);
                    if (modalData && modalData.config.onAction) {
                        modalData.config.onAction(action, modalId, e);
                    }
                    
                    // Emit custom event
                    const event = new CustomEvent('modalAction', {
                        detail: { action, modalId, button }
                    });
                    document.dispatchEvent(event);
                }
            });
        });
    }

    /**
     * Close a modal
     * @param {string} modalId - Modal ID to close
     */
    close(modalId) {
        const modalData = this.modals.get(modalId);
        if (!modalData) return;

        const { element, config } = modalData;
        
        // Hide with animation
        element.classList.remove('active');
        
        setTimeout(() => {
            if (element.parentNode) {
                element.parentNode.removeChild(element);
            }
            this.modals.delete(modalId);
            
            // Remove from stack
            const index = this.modalStack.indexOf(modalId);
            if (index > -1) {
                this.modalStack.splice(index, 1);
            }
            
            // Manage body scroll
            this.updateBodyScroll();
            
            if (config.onHide) {
                config.onHide(modalId);
            }
        }, 300);
    }

    /**
     * Close all modals
     */
    closeAll() {
        [...this.modalStack].forEach(modalId => {
            this.close(modalId);
        });
    }

    /**
     * Update modal content
     * @param {string} modalId - Modal ID
     * @param {string} content - New content
     */
    updateContent(modalId, content) {
        const modalData = this.modals.get(modalId);
        if (!modalData) return;

        const body = modalData.element.querySelector('.modal-body');
        if (body) {
            body.innerHTML = content;
        }
    }

    /**
     * Update modal title
     * @param {string} modalId - Modal ID
     * @param {string} title - New title
     */
    updateTitle(modalId, title) {
        const modalData = this.modals.get(modalId);
        if (!modalData) return;

        const titleElement = modalData.element.querySelector('.modal-title');
        if (titleElement) {
            titleElement.textContent = title;
        }
    }

    /**
     * Show loading state in modal
     * @param {string} modalId - Modal ID
     * @param {string} message - Loading message
     */
    showLoading(modalId, message = 'Loading...') {
        const content = `
            <div class="loading-modal">
                <div class="loading-spinner">
                    <i class="fas fa-spinner fa-spin"></i>
                </div>
                <p class="loading-text">${message}</p>
            </div>
        `;
        this.updateContent(modalId, content);
    }

    /**
     * Show alert modal
     * @param {string} message - Alert message
     * @param {object} options - Alert options
     */
    alert(message, options = {}) {
        return new Promise((resolve) => {
            const config = {
                title: options.title || 'Alert',
                content: `<p>${message}</p>`,
                size: options.size || 'sm',
                buttons: [
                    {
                        text: options.buttonText || 'OK',
                        class: 'btn-primary',
                        action: 'ok',
                        dismiss: true
                    }
                ],
                onAction: (action) => {
                    if (action === 'ok') {
                        resolve(true);
                    }
                },
                onHide: () => resolve(true),
                ...options
            };

            this.show(config);
        });
    }

    /**
     * Show confirm modal
     * @param {string} message - Confirmation message
     * @param {object} options - Confirm options
     */
    confirm(message, options = {}) {
        return new Promise((resolve) => {
            const config = {
                title: options.title || 'Confirm',
                content: `<p>${message}</p>`,
                size: options.size || 'sm',
                buttons: [
                    {
                        text: options.cancelText || 'Cancel',
                        class: 'btn-secondary',
                        action: 'cancel',
                        dismiss: true
                    },
                    {
                        text: options.confirmText || 'Confirm',
                        class: options.confirmClass || 'btn-primary',
                        action: 'confirm',
                        dismiss: true
                    }
                ],
                onAction: (action) => {
                    resolve(action === 'confirm');
                },
                onHide: () => resolve(false),
                ...options
            };

            this.show(config);
        });
    }

    /**
     * Show prompt modal
     * @param {string} message - Prompt message
     * @param {object} options - Prompt options
     */
    prompt(message, options = {}) {
        return new Promise((resolve) => {
            const inputId = 'modal-prompt-' + Date.now();
            const content = `
                <p>${message}</p>
                <div style="margin-top: 1rem;">
                    <input type="text" id="${inputId}" class="form-input" 
                           placeholder="${options.placeholder || ''}" 
                           value="${options.defaultValue || ''}" 
                           style="width: 100%; padding: 0.75rem; border: 1px solid #d1d5db; border-radius: 0.375rem; font-size: 0.875rem;">
                </div>
            `;

            const config = {
                title: options.title || 'Input',
                content: content,
                size: options.size || 'sm',
                buttons: [
                    {
                        text: options.cancelText || 'Cancel',
                        class: 'btn-secondary',
                        action: 'cancel',
                        dismiss: true
                    },
                    {
                        text: options.confirmText || 'OK',
                        class: 'btn-primary',
                        action: 'confirm',
                        dismiss: true
                    }
                ],
                onShow: () => {
                    setTimeout(() => {
                        const input = document.getElementById(inputId);
                        if (input) {
                            input.focus();
                            input.select();
                        }
                    }, 100);
                },
                onAction: (action) => {
                    if (action === 'confirm') {
                        const input = document.getElementById(inputId);
                        resolve(input ? input.value : '');
                    } else {
                        resolve(null);
                    }
                },
                onHide: () => resolve(null),
                ...options
            };

            const modalId = this.show(config);

            // Handle enter key in input
            setTimeout(() => {
                const input = document.getElementById(inputId);
                if (input) {
                    input.addEventListener('keydown', (e) => {
                        if (e.key === 'Enter') {
                            resolve(input.value);
                            this.close(modalId);
                        }
                    });
                }
            }, 100);
        });
    }

    /**
     * Show image modal
     * @param {string} src - Image source
     * @param {object} options - Image modal options
     */
    showImage(src, options = {}) {
        const content = `
            <div class="image-modal">
                <img src="${src}" alt="${options.alt || ''}" class="modal-image">
            </div>
        `;

        return this.show({
            content: content,
            size: 'lg',
            className: 'image-modal',
            closable: true,
            ...options
        });
    }

    /**
     * Show form modal
     * @param {string} formHtml - Form HTML content
     * @param {object} options - Form modal options
     */
    showForm(formHtml, options = {}) {
        return new Promise((resolve) => {
            const config = {
                title: options.title || 'Form',
                content: formHtml,
                size: options.size || 'md',
                buttons: [
                    {
                        text: options.cancelText || 'Cancel',
                        class: 'btn-secondary',
                        action: 'cancel',
                        dismiss: true
                    },
                    {
                        text: options.submitText || 'Submit',
                        class: 'btn-primary',
                        action: 'submit'
                    }
                ],
                onAction: (action, modalId) => {
                    if (action === 'submit') {
                        const modal = this.modals.get(modalId);
                        const form = modal.element.querySelector('form');
                        
                        if (form) {
                            const formData = new FormData(form);
                            const data = Object.fromEntries(formData.entries());
                            
                            if (options.onSubmit) {
                                const result = options.onSubmit(data, form);
                                if (result !== false) {
                                    this.close(modalId);
                                    resolve(data);
                                }
                            } else {
                                this.close(modalId);
                                resolve(data);
                            }
                        }
                    } else {
                        resolve(null);
                    }
                },
                onHide: () => resolve(null),
                ...options
            };

            this.show(config);
        });
    }

    /**
     * Update body scroll behavior
     */
    updateBodyScroll() {
        if (this.modalStack.length > 0) {
            document.body.style.overflow = 'hidden';
            document.body.classList.add('modal-open');
        } else {
            document.body.style.overflow = '';
            document.body.classList.remove('modal-open');
        }
    }

    /**
     * Check if modal is open
     * @param {string} modalId - Modal ID (optional)
     */
    isOpen(modalId = null) {
        if (modalId) {
            return this.modals.has(modalId);
        }
        return this.modalStack.length > 0;
    }

    /**
     * Get modal element
     * @param {string} modalId - Modal ID
     */
    getModal(modalId) {
        const modalData = this.modals.get(modalId);
        return modalData ? modalData.element : null;
    }

    /**
     * Set modal size
     * @param {string} modalId - Modal ID
     * @param {string} size - New size (sm, md, lg, xl, fullscreen)
     */
    setSize(modalId, size) {
        const modalData = this.modals.get(modalId);
        if (!modalData) return;

        const modal = modalData.element.querySelector('.modal');
        if (modal) {
            modal.className = modal.className.replace(/modal-(sm|md|lg|xl|fullscreen)/, `modal-${size}`);
        }
    }

    /**
     * Enable/disable backdrop click to close
     * @param {boolean} enabled - Whether to enable backdrop click close
     */
    setBackdropClose(enabled) {
        this.backdropClickClose = enabled;
    }

    /**
     * Enable/disable escape key to close
     * @param {boolean} enabled - Whether to enable escape key close
     */
    setEscapeClose(enabled) {
        this.escapeKeyClose = enabled;
    }

    /**
     * Generate unique ID for modal
     */
    generateId() {
        return 'modal-' + Date.now() + '-' + Math.random().toString(36).substr(2, 9);
    }

    /**
     * Get modal count
     */
    getCount() {
        return this.modalStack.length;
    }

    /**
     * Get active modal ID
     */
    getActiveModalId() {
        return this.modalStack.length > 0 ? this.modalStack[this.modalStack.length - 1] : null;
    }
}

// Initialize modal manager
window.ModalManager = ModalManager;
