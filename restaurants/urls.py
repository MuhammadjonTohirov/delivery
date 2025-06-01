from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    RestaurantStatisticsViewSet,
    RestaurantViewSet,
    MenuCategoryViewSet,
    MenuItemViewSet,
    RestaurantReviewViewSet
)

# Create a router and register our viewsets with it
router = DefaultRouter()
router.register(r'list', RestaurantViewSet, basename='restaurant')
router.register(r'categories', MenuCategoryViewSet, basename='category')
router.register(r'menu-items', MenuItemViewSet, basename='menu-item')
router.register(r'reviews', RestaurantReviewViewSet, basename='review')
router.register(r'statistics', RestaurantStatisticsViewSet, basename='statistics')

app_name = 'restaurants'

urlpatterns = [
    path('', include(router.urls)),
]