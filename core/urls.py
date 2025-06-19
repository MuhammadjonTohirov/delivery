"""
Core app URL configuration
"""
from django.urls import path
from . import views

urlpatterns = [
    path('search/', views.global_search, name='global-search'),
    path('search/suggestions/', views.search_suggestions, name='search-suggestions'),
]