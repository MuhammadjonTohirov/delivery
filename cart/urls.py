from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CartViewSet, SavedCartViewSet, CartAbandonmentViewSet

router = DefaultRouter()
router.register(r'', CartViewSet, basename='cart')
router.register(r'saved', SavedCartViewSet, basename='saved-cart')
router.register(r'abandonment', CartAbandonmentViewSet, basename='cart-abandonment')

app_name = 'cart'

urlpatterns = [
    path('', include(router.urls)),
]
