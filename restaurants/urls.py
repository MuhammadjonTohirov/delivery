from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RestaurantViewSet, MenuCategoryViewSet, MenuItemViewSet, RestaurantReviewViewSet

router = DefaultRouter()
router.register(r'list', RestaurantViewSet, basename='restaurant')
router.register(r'categories', MenuCategoryViewSet, basename='category')
router.register(r'menu-items', MenuItemViewSet, basename='menu-item')
router.register(r'reviews', RestaurantReviewViewSet, basename='review')
router.register(r'mine', RestaurantViewSet, basename='mine') # This line is redundant.
# restaurants/${restaurant_id}/statistics/ is not included in the router, as it is a custom endpoint.
router.register(r'(?P<restaurant_id>[^/.]+)/statistics', RestaurantViewSet, basename='restaurant-statistics')

app_name = 'restaurants'

urlpatterns = [
    path('', include(router.urls)),
]