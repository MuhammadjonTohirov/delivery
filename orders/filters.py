import django_filters
from django.db.models import Q
from .models import Order
from restaurants.models import Restaurant, MenuCategory


class OrderFilter(django_filters.FilterSet):
    """
    Filter class for Order model with support for:
    - Restaurant filtering
    - Date range filtering
    - Category (menu category) filtering
    - Status filtering
    - Search by customer name or order ID
    """
    
    # Restaurant filter
    restaurant = django_filters.ModelChoiceFilter(
        queryset=Restaurant.objects.all(),
        field_name='restaurant',
        to_field_name='id'
    )
    
    # Date range filters
    date_from = django_filters.DateFilter(
        field_name='created_at',
        lookup_expr='date__gte'
    )
    date_to = django_filters.DateFilter(
        field_name='created_at',
        lookup_expr='date__lte'
    )
    
    # Category filter (based on menu items in the order)
    category = django_filters.ModelChoiceFilter(
        queryset=MenuCategory.objects.all(),
        method='filter_by_category',
        to_field_name='id'
    )
    
    # Status filter
    status = django_filters.ChoiceFilter(
        choices=Order.ORDER_STATUS_CHOICES,
        field_name='status'
    )
    
    # Search filter for customer name or order ID
    search = django_filters.CharFilter(
        method='filter_search'
    )
    
    class Meta:
        model = Order
        fields = ['restaurant', 'date_from', 'date_to', 'category', 'status', 'search']
    
    def filter_by_category(self, queryset, name, value):
        """Filter orders that contain items from the specified category"""
        if value:
            return queryset.filter(items__menu_item__category=value).distinct()
        return queryset
    
    def filter_search(self, queryset, name, value):
        """Search by customer name or order ID"""
        if value:
            return queryset.filter(
                Q(customer__first_name__icontains=value) |
                Q(customer__last_name__icontains=value) |
                Q(id__icontains=value)
            ).distinct()
        return queryset