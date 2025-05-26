from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RestaurantStatisticsView, RestaurantViewSet, MenuCategoryViewSet, MenuItemViewSet, RestaurantReviewViewSet

router = DefaultRouter()
router.register(r'list', RestaurantViewSet, basename='restaurant')
router.register(r'categories', MenuCategoryViewSet, basename='category')
router.register(r'menu-items', MenuItemViewSet, basename='menu-item')
router.register(r'reviews', RestaurantReviewViewSet, basename='review')
router.register(r'mine', RestaurantViewSet, basename='mine') # This line is redundant.
router.register(r'statistics', RestaurantStatisticsView, basename='statistics')

app_name = 'restaurants'

urlpatterns = [
    path('', include(router.urls)),
]