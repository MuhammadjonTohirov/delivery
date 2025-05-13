from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RestaurantViewSet, MenuCategoryViewSet, MenuItemViewSet, RestaurantReviewViewSet

router = DefaultRouter()
router.register(r'restaurants', RestaurantViewSet, basename='restaurant')
router.register(r'categories', MenuCategoryViewSet, basename='category')
router.register(r'menu-items', MenuItemViewSet, basename='menu-item')
router.register(r'reviews', RestaurantReviewViewSet, basename='review')

app_name = 'restaurants'

urlpatterns = [
    path('', include(router.urls)),
]