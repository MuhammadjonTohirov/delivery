from django.shortcuts import render
from django.views.generic import TemplateView

class HomePageView(TemplateView):
    template_name = "home.html"

class LoginPageView(TemplateView):
    template_name = "login.html"

class RegisterPageView(TemplateView):
    template_name = "register.html"

# Placeholder views for different user dashboards
class CustomerDashboardView(TemplateView):
    template_name = "dashboards/customer_dashboard.html"

class RestaurantDashboardView(TemplateView):
    template_name = "dashboards/restaurant_dashboard.html"

class DriverDashboardView(TemplateView):
    template_name = "dashboards/driver_dashboard.html"

class ProfilePageView(TemplateView):
    template_name = "profile.html"

class RestaurantListView(TemplateView):
    template_name = "restaurants/restaurant_list.html"

class RestaurantDetailView(TemplateView):
    template_name = "restaurants/restaurant_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['restaurant_id'] = self.kwargs['restaurant_id']
        return context

class ManageRestaurantView(TemplateView):
    template_name = "restaurants/manage_restaurant.html"

class MenuManagementView(TemplateView):
    template_name = "restaurants/manage_menu.html"

class MenuCategoryCreateView(TemplateView):
    template_name = "restaurants/category_form.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_type'] = 'Create Category'
        return context

class MenuCategoryEditView(TemplateView):
    template_name = "restaurants/category_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_type'] = 'Edit Category'
        context['category_id'] = self.kwargs['category_id']
        return context

class MenuItemCreateView(TemplateView):
    template_name = "restaurants/menu_item_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_type'] = 'Create Menu Item'
        # If creating an item under a specific category:
        if 'category_id' in self.kwargs:
            context['category_id'] = self.kwargs['category_id']
        return context

class MenuItemEditView(TemplateView):
    template_name = "restaurants/menu_item_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_type'] = 'Edit Menu Item'
        context['item_id'] = self.kwargs['item_id']
        return context

class RestaurantOrderListView(TemplateView):
    template_name = "restaurants/restaurant_orders.html"

class DriverTaskListView(TemplateView):
    template_name = "drivers/task_list.html"

class DriverEarningsView(TemplateView):
    template_name = "drivers/earnings_report.html"
