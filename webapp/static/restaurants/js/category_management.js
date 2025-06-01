/**
 * Category Management JavaScript
 * Handles all category CRUD operations with AJAX
 */

class CategoryManager {
    static currentCategory = null;
    static categories = [];
    static apiBaseUrl = '/api/restaurants/categories/';

    static init() {
        this.setupEventListeners();
        this.loadCategories();
    }

    static setupEventListeners() {
        // Add category button
        document.getElementById('addCategoryBtn').addEventListener('click', () => {
            this.showAddForm();
        });

        // Save category button
        document.getElementById('saveCategoryBtn').addEventListener('click', () => {
            this.saveCategory();
        });

        // Delete confirmation button
        document.getElementById('confirmDeleteBtn').addEventListener('click', () => {
            this.confirmDelete();
        });

        // Form validation on input
        document.getElementById('categoryName').addEventListener('input', (e) => {
            this.validateField(e.target);
        });
    }

    static async loadCategories() {
        try {
            this.showLoading(true);
            const response = await this.makeRequest('GET', this.apiBaseUrl);
            
            if (response.ok) {
                const data = await response.json();
                this.categories = data.results || data;
                this.renderCategories();
            } else {
                this.showError('Failed to load categories');
            }
        } catch (error) {
            console.error('Error loading categories:', error);
            this.showError('Failed to load categories');
        } finally {
            this.showLoading(false);
        }
    }

    static renderCategories() {
        const container = document.getElementById('categoriesList');
        const emptyState = document.getElementById('emptyState');

        if (this.categories.length === 0) {
            container.style.display = 'none';
            emptyState.style.display = 'block';
            return;
        }

        container.style.display = 'block';
        emptyState.style.display = 'none';

        // Sort categories by order
        const sortedCategories = [...this.categories].sort((a, b) => a.order - b.order);

        container.innerHTML = sortedCategories.map(category => `
            <div class="category-card fade-in" data-category-id="${category.id}" draggable="true">
                <div class="category-card-header">
                    <div class="category-info">
                        <h3>${this.escapeHtml(category.name)}</h3>
                        ${category.description ? `<p>${this.escapeHtml(category.description)}</p>` : ''}
                    </div>
                    <div class="category-stats">
                        <span class="stat-badge items-count">${category.items_count || 0} items</span>
                        <span class="stat-badge order-badge">Order: ${category.order}</span>
                    </div>
                    <div class="category-actions">
                        <button class="btn-icon btn-drag" title="Drag to reorder">
                            <i class="fas fa-grip-vertical"></i>
                        </button>
                        <button class="btn-icon btn-edit" onclick="CategoryManager.editCategory('${category.id}')" title="Edit">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button class="btn-icon btn-delete" onclick="CategoryManager.deleteCategory('${category.id}')" title="Delete">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </div>
            </div>
        `).join('');

        this.setupDragAndDrop();
    }

    static setupDragAndDrop() {
        const cards = document.querySelectorAll('.category-card');
        
        cards.forEach(card => {
            card.addEventListener('dragstart', (e) => {
                card.classList.add('dragging');
                e.dataTransfer.setData('text/plain', card.dataset.categoryId);
            });

            card.addEventListener('dragend', () => {
                card.classList.remove('dragging');
            });

            card.addEventListener('dragover', (e) => {
                e.preventDefault();
                card.classList.add('drag-over');
            });

            card.addEventListener('dragleave', () => {
                card.classList.remove('drag-over');
            });

            card.addEventListener('drop', (e) => {
                e.preventDefault();
                card.classList.remove('drag-over');
                
                const draggedId = e.dataTransfer.getData('text/plain');
                const targetId = card.dataset.categoryId;
                
                if (draggedId !== targetId) {
                    this.reorderCategories(draggedId, targetId);
                }
            });
        });
    }

    static async reorderCategories(draggedId, targetId) {
        try {
            const draggedIndex = this.categories.findIndex(c => c.id === draggedId);
            const targetIndex = this.categories.findIndex(c => c.id === targetId);
            
            if (draggedIndex === -1 || targetIndex === -1) return;

            // Reorder locally first for immediate feedback
            const draggedCategory = this.categories[draggedIndex];
            this.categories.splice(draggedIndex, 1);
            this.categories.splice(targetIndex, 0, draggedCategory);

            // Update order values
            this.categories.forEach((category, index) => {
                category.order = index;
            });

            this.renderCategories();

            // Send reorder request to server
            const reorderData = this.categories.map(category => ({
                id: category.id,
                order: category.order
            }));

            const response = await this.makeRequest('POST', `${this.apiBaseUrl}reorder/`, {
                categories: reorderData
            });

            if (!response.ok) {
                throw new Error('Failed to save order');
            }

            this.showSuccess('Categories reordered successfully');
        } catch (error) {
            console.error('Error reordering categories:', error);
            this.showError('Failed to reorder categories');
            // Reload to reset order
            this.loadCategories();
        }
    }

    static showAddForm() {
        this.currentCategory = null;
        document.getElementById('categoryModalLabel').textContent = 'Add Category';
        document.getElementById('categoryForm').reset();
        this.clearValidation();
        
        const modal = new bootstrap.Modal(document.getElementById('categoryModal'));
        modal.show();
    }

    static editCategory(categoryId) {
        const category = this.categories.find(c => c.id === categoryId);
        if (!category) return;

        this.currentCategory = category;
        document.getElementById('categoryModalLabel').textContent = 'Edit Category';
        
        // Populate form
        document.getElementById('categoryName').value = category.name;
        document.getElementById('categoryDescription').value = category.description || '';
        document.getElementById('categoryOrder').value = category.order;
        
        this.clearValidation();
        
        const modal = new bootstrap.Modal(document.getElementById('categoryModal'));
        modal.show();
    }

    static async saveCategory() {
        const form = document.getElementById('categoryForm');
        const saveBtn = document.getElementById('saveCategoryBtn');
        const spinner = saveBtn.querySelector('.spinner-border');

        // Validate form
        if (!this.validateForm(form)) {
            return;
        }

        try {
            spinner.style.display = 'inline-block';
            saveBtn.disabled = true;

            const formData = new FormData(form);
            const categoryData = {
                name: formData.get('name'),
                description: formData.get('description') || '',
                order: parseInt(formData.get('order')) || 0
            };

            let response;
            if (this.currentCategory) {
                // Update existing category
                response = await this.makeRequest('PATCH', `${this.apiBaseUrl}${this.currentCategory.id}/`, categoryData);
            } else {
                // Create new category
                response = await this.makeRequest('POST', this.apiBaseUrl, categoryData);
            }

            if (response.ok) {
                const savedCategory = await response.json();
                
                if (this.currentCategory) {
                    // Update existing category in local array
                    const index = this.categories.findIndex(c => c.id === this.currentCategory.id);
                    this.categories[index] = savedCategory;
                } else {
                    // Add new category to local array
                    this.categories.push(savedCategory);
                }

                this.renderCategories();
                this.showSuccess(`Category ${this.currentCategory ? 'updated' : 'created'} successfully`);
                
                // Close modal
                const modal = bootstrap.Modal.getInstance(document.getElementById('categoryModal'));
                modal.hide();
            } else {
                const errorData = await response.json();
                this.handleFormErrors(errorData);
            }
        } catch (error) {
            console.error('Error saving category:', error);
            this.showError('Failed to save category');
        } finally {
            spinner.style.display = 'none';
            saveBtn.disabled = false;
        }
    }

    static deleteCategory(categoryId) {
        const category = this.categories.find(c => c.id === categoryId);
        if (!category) return;

        this.currentCategory = category;
        
        document.getElementById('deleteDetails').innerHTML = `
            <div class="alert alert-warning">
                <strong>Category:</strong> ${this.escapeHtml(category.name)}<br>
                <strong>Items in category:</strong> ${category.items_count || 0}
            </div>
        `;

        const modal = new bootstrap.Modal(document.getElementById('deleteModal'));
        modal.show();
    }

    static async confirmDelete() {
        if (!this.currentCategory) return;

        const deleteBtn = document.getElementById('confirmDeleteBtn');
        const spinner = deleteBtn.querySelector('.spinner-border');

        try {
            spinner.style.display = 'inline-block';
            deleteBtn.disabled = true;

            const response = await this.makeRequest('DELETE', `${this.apiBaseUrl}${this.currentCategory.id}/`);

            if (response.ok) {
                // Remove from local array
                this.categories = this.categories.filter(c => c.id !== this.currentCategory.id);
                this.renderCategories();
                this.showSuccess('Category deleted successfully');
                
                // Close modal
                const modal = bootstrap.Modal.getInstance(document.getElementById('deleteModal'));
                modal.hide();
            } else {
                this.showError('Failed to delete category');
            }
        } catch (error) {
            console.error('Error deleting category:', error);
            this.showError('Failed to delete category');
        } finally {
            spinner.style.display = 'none';
            deleteBtn.disabled = false;
        }
    }

    static validateForm(form) {
        let isValid = true;
        const nameField = form.querySelector('#categoryName');

        if (!nameField.value.trim()) {
            this.showFieldError(nameField, 'Category name is required');
            isValid = false;
        } else if (nameField.value.trim().length > 50) {
            this.showFieldError(nameField, 'Category name must be 50 characters or less');
            isValid = false;
        } else {
            this.clearFieldError(nameField);
        }

        return isValid;
    }

    static validateField(field) {
        if (field.id === 'categoryName') {
            if (!field.value.trim()) {
                this.showFieldError(field, 'Category name is required');
            } else if (field.value.trim().length > 50) {
                this.showFieldError(field, 'Category name must be 50 characters or less');
            } else {
                this.clearFieldError(field);
            }
        }
    }

    static showFieldError(field, message) {
        field.classList.add('is-invalid');
        const feedback = field.parentNode.querySelector('.invalid-feedback');
        if (feedback) {
            feedback.textContent = message;
        }
    }

    static clearFieldError(field) {
        field.classList.remove('is-invalid');
        const feedback = field.parentNode.querySelector('.invalid-feedback');
        if (feedback) {
            feedback.textContent = '';
        }
    }

    static clearValidation() {
        const form = document.getElementById('categoryForm');
        form.querySelectorAll('.is-invalid').forEach(field => {
            field.classList.remove('is-invalid');
        });
        form.querySelectorAll('.invalid-feedback').forEach(feedback => {
            feedback.textContent = '';
        });
    }

    static handleFormErrors(errorData) {
        if (errorData.name) {
            this.showFieldError(document.getElementById('categoryName'), errorData.name[0]);
        }
        if (errorData.non_field_errors) {
            this.showError(errorData.non_field_errors[0]);
        }
    }

    static async makeRequest(method, url, data = null) {
        const options = {
            method: method,
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.getCSRFToken()
            },
            credentials: 'same-origin'
        };

        if (data) {
            options.body = JSON.stringify(data);
        }

        return fetch(url, options);
    }

    static getCSRFToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]')?.value || 
               document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '';
    }

    static showLoading(show) {
        const spinner = document.getElementById('loadingSpinner');
        spinner.style.display = show ? 'flex' : 'none';
    }

    static showSuccess(message) {
        this.showAlert(message, 'success');
    }

    static showError(message) {
        this.showAlert(message, 'danger');
    }

    static showAlert(message, type) {
        // Remove existing alerts
        document.querySelectorAll('.alert').forEach(alert => alert.remove());

        const alertHtml = `
            <div class="alert alert-${type} alert-dismissible fade show" role="alert">
                ${this.escapeHtml(message)}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `;

        const container = document.querySelector('.container-fluid');
        container.insertAdjacentHTML('afterbegin', alertHtml);

        // Auto-remove after 5 seconds
        setTimeout(() => {
            const alert = document.querySelector('.alert');
            if (alert) {
                alert.remove();
            }
        }, 5000);
    }

    static escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Export for use in other modules if needed
window.CategoryManager = CategoryManager;
