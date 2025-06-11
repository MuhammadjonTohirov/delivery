from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    PromotionViewSet, PromotionUsageViewSet, CampaignViewSet,
    LoyaltyProgramViewSet, CustomerLoyaltyAccountViewSet, LoyaltyTransactionViewSet
)

app_name = 'promotions'

# Create router and register viewsets
router = DefaultRouter()
router.register(r'promotions', PromotionViewSet, basename='promotion')
router.register(r'promotion-usage', PromotionUsageViewSet, basename='promotion-usage')
router.register(r'campaigns', CampaignViewSet, basename='campaign')
router.register(r'loyalty-programs', LoyaltyProgramViewSet, basename='loyalty-program')
router.register(r'loyalty-accounts', CustomerLoyaltyAccountViewSet, basename='loyalty-account')
router.register(r'loyalty-transactions', LoyaltyTransactionViewSet, basename='loyalty-transaction')

urlpatterns = [
    path('', include(router.urls)),
]
