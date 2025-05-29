from django.contrib import admin
from .models import (
    PromotionCampaign, Coupon, CouponUsage, LoyaltyProgram, LoyaltyAccount,
    LoyaltyTransaction, ReferralProgram, Referral, FlashSale
)


@admin.register(PromotionCampaign)
class PromotionCampaignAdmin(admin.ModelAdmin):
    list_display = ['name', 'type', 'status', 'start_date', 'end_date', 'current_uses', 'max_uses_total']
    list_filter = ['type', 'status', 'target_new_users_only']
    search_fields = ['name', 'description']
    filter_horizontal = ['restaurants', 'menu_items']


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'discount_type', 'discount_value', 'is_active', 'current_uses', 'max_uses']
    list_filter = ['discount_type', 'is_active', 'first_order_only']
    search_fields = ['code', 'name']
    filter_horizontal = ['applicable_restaurants', 'applicable_menu_items']


@admin.register(CouponUsage)
class CouponUsageAdmin(admin.ModelAdmin):
    list_display = ['coupon', 'user', 'order', 'discount_amount', 'created_at']
    list_filter = ['created_at']
    search_fields = ['coupon__code', 'user__email', 'order__id']


@admin.register(LoyaltyProgram)
class LoyaltyProgramAdmin(admin.ModelAdmin):
    list_display = ['name', 'points_per_dollar', 'points_redemption_value', 'min_points_redemption', 'is_active']
    list_filter = ['is_active']


@admin.register(LoyaltyAccount)
class LoyaltyAccountAdmin(admin.ModelAdmin):
    list_display = ['user', 'program', 'points_balance', 'total_points_earned', 'total_points_redeemed']
    search_fields = ['user__email', 'user__full_name']
    list_filter = ['program']


@admin.register(LoyaltyTransaction)
class LoyaltyTransactionAdmin(admin.ModelAdmin):
    list_display = ['account', 'type', 'points', 'description', 'created_at']
    list_filter = ['type', 'created_at']
    search_fields = ['account__user__email', 'description']


@admin.register(ReferralProgram)
class ReferralProgramAdmin(admin.ModelAdmin):
    list_display = ['name', 'referrer_reward_type', 'referrer_reward_value', 'referee_reward_type', 'referee_reward_value', 'is_active']
    list_filter = ['is_active', 'referrer_reward_type', 'referee_reward_type']


@admin.register(Referral)
class ReferralAdmin(admin.ModelAdmin):
    list_display = ['referrer', 'referee', 'program', 'referral_code', 'status', 'completed_at']
    list_filter = ['status', 'program']
    search_fields = ['referrer__email', 'referee__email', 'referral_code']


@admin.register(FlashSale)
class FlashSaleAdmin(admin.ModelAdmin):
    list_display = ['name', 'discount_percentage', 'start_time', 'end_time', 'current_orders', 'max_orders', 'is_active']
    list_filter = ['is_active', 'start_time']
    search_fields = ['name', 'description']
    filter_horizontal = ['restaurants', 'menu_items']
