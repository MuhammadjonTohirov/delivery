from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CartViewSet, CustomerFavoriteViewSet, SavedCartViewSet, 
    QuickReorderViewSet, RecentOrderViewSet, MenuItemCustomizationViewSet
)

router = DefaultRouter()
router.register(r'cart', CartViewSet, basename='cart')
router.register(r'favorites', CustomerFavoriteViewSet, basename='favorite')
router.register(r'saved-carts', SavedCartViewSet, basename='saved-cart')
router.register(r'quick-reorders', QuickReorderViewSet, basename='quick-reorder')
router.register(r'recent-orders', RecentOrderViewSet, basename='recent-order')
router.register(r'customizations', MenuItemCustomizationViewSet, basename='customization')

app_name = 'cart'

urlpatterns = [
    path('', include(router.urls)),
]
