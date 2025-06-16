from django.urls import path
from .customer_views import customers_list, customer_summary

app_name = 'customers'

urlpatterns = [
    path('', customers_list, name='customers-list'),
    path('<str:customer_id>/summary/', customer_summary, name='customer-summary'),
]