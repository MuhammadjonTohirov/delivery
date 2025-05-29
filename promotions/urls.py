from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    PromotionCampaignViewSet, CouponViewSet, CouponUsageViewSet,
    LoyaltyProgramViewSet, LoyaltyAccountViewSet, ReferralProgramViewSet,
    ReferralViewSet, FlashSaleViewSet
)

router = DefaultRouter()
router.register(r'campaigns', PromotionCampaignViewSet, basename='campaign')
router.register(r'coupons', CouponViewSet, basename='coupon')
router.register(r'coupon-usage', CouponUsageViewSet, basename='coupon-usage')
router.register(r'loyalty-programs', LoyaltyProgramViewSet, basename='loyalty-program')
router.register(r'loyalty-account', LoyaltyAccountViewSet, basename='loyalty-account')
router.register(r'referral-programs', ReferralProgramViewSet, basename='referral-program')
router.register(r'referrals', ReferralViewSet, basename='referral')
router.register(r'flash-sales', FlashSaleViewSet, basename='flash-sale')

app_name = 'promotions'

urlpatterns = [
    path('', include(router.urls)),
]
