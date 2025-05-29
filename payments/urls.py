from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PaymentMethodViewSet, PaymentViewSet, WalletViewSet, PaymentRefundViewSet

router = DefaultRouter()
router.register(r'methods', PaymentMethodViewSet, basename='payment-method')
router.register(r'payments', PaymentViewSet, basename='payment')
router.register(r'wallet', WalletViewSet, basename='wallet')
router.register(r'refunds', PaymentRefundViewSet, basename='payment-refund')

app_name = 'payments'

urlpatterns = [
    path('', include(router.urls)),
]
