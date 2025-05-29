from rest_framework import serializers
from django.utils import timezone
from .models import (
    PromotionCampaign, Coupon, CouponUsage, LoyaltyProgram, LoyaltyAccount,
    LoyaltyTransaction, ReferralProgram, Referral, FlashSale
)


class PromotionCampaignSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source='created_by.full_name', read_only=True)
    is_active = serializers.BooleanField(read_only=True)
    restaurants = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    menu_items = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    
    class Meta:
        model = PromotionCampaign
        fields = ['id', 'name', 'description', 'type', 'status', 'start_date', 'end_date',
                  'max_uses_total', 'max_uses_per_user', 'current_uses', 'restaurants', 
                  'menu_items', 'min_order_amount', 'target_user_roles', 'target_new_users_only',
                  'created_by', 'created_by_name', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['id', 'current_uses', 'created_by', 'created_by_name', 
                           'is_active', 'created_at', 'updated_at']
    
    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class CouponSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source='created_by.full_name', read_only=True)
    is_valid = serializers.BooleanField(read_only=True)
    applicable_restaurants = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    applicable_menu_items = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    
    class Meta:
        model = Coupon
        fields = ['id', 'code', 'name', 'description', 'discount_type', 'discount_value',
                  'max_discount_amount', 'min_order_amount', 'start_date', 'end_date',
                  'max_uses', 'max_uses_per_user', 'current_uses', 'is_active',
                  'applicable_restaurants', 'applicable_menu_items', 'first_order_only',
                  'created_by', 'created_by_name', 'is_valid', 'created_at', 'updated_at']
        read_only_fields = ['id', 'current_uses', 'created_by', 'created_by_name', 
                           'is_valid', 'created_at', 'updated_at']
    
    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class CouponUsageSerializer(serializers.ModelSerializer):
    coupon_code = serializers.CharField(source='coupon.code', read_only=True)
    user_name = serializers.CharField(source='user.full_name', read_only=True)
    order_id = serializers.UUIDField(source='order.id', read_only=True)
    
    class Meta:
        model = CouponUsage
        fields = ['id', 'coupon', 'coupon_code', 'user', 'user_name', 'order', 'order_id',
                  'discount_amount', 'created_at']
        read_only_fields = ['id', 'coupon_code', 'user_name', 'order_id', 'created_at']


class CouponValidationSerializer(serializers.Serializer):
    """Serializer for validating coupon codes"""
    code = serializers.CharField(max_length=20)
    order_amount = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    restaurant_id = serializers.UUIDField(required=False)
    
    def validate_code(self, value):
        try:
            coupon = Coupon.objects.get(code=value.upper())
            if not coupon.is_valid:
                raise serializers.ValidationError("This coupon is expired or no longer valid.")
            return value.upper()
        except Coupon.DoesNotExist:
            raise serializers.ValidationError("Invalid coupon code.")


class LoyaltyProgramSerializer(serializers.ModelSerializer):
    class Meta:
        model = LoyaltyProgram
        fields = ['id', 'name', 'description', 'points_per_dollar', 'points_redemption_value',
                  'min_points_redemption', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class LoyaltyAccountSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.full_name', read_only=True)
    program_name = serializers.CharField(source='program.name', read_only=True)
    
    class Meta:
        model = LoyaltyAccount
        fields = ['id', 'user', 'user_name', 'program', 'program_name', 'points_balance',
                  'total_points_earned', 'total_points_redeemed', 'created_at', 'updated_at']
        read_only_fields = ['id', 'user_name', 'program_name', 'points_balance',
                           'total_points_earned', 'total_points_redeemed', 'created_at', 'updated_at']


class LoyaltyTransactionSerializer(serializers.ModelSerializer):
    account_user_name = serializers.CharField(source='account.user.full_name', read_only=True)
    
    class Meta:
        model = LoyaltyTransaction
        fields = ['id', 'account', 'account_user_name', 'type', 'points', 'description',
                  'reference_order', 'balance_before', 'balance_after', 'created_at']
        read_only_fields = ['id', 'account_user_name', 'balance_before', 'balance_after', 'created_at']


class ReferralProgramSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReferralProgram
        fields = ['id', 'name', 'description', 'referrer_reward_type', 'referrer_reward_value',
                  'referee_reward_type', 'referee_reward_value', 'min_referee_orders',
                  'min_referee_order_amount', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class ReferralSerializer(serializers.ModelSerializer):
    referrer_name = serializers.CharField(source='referrer.full_name', read_only=True)
    referee_name = serializers.CharField(source='referee.full_name', read_only=True)
    program_name = serializers.CharField(source='program.name', read_only=True)
    
    class Meta:
        model = Referral
        fields = ['id', 'referrer', 'referrer_name', 'referee', 'referee_name', 'program',
                  'program_name', 'referral_code', 'status', 'referee_orders_count',
                  'referee_total_spent', 'completed_at', 'created_at', 'updated_at']
        read_only_fields = ['id', 'referrer_name', 'referee_name', 'program_name',
                           'referral_code', 'referee_orders_count', 'referee_total_spent',
                           'completed_at', 'created_at', 'updated_at']


class FlashSaleSerializer(serializers.ModelSerializer):
    is_ongoing = serializers.BooleanField(read_only=True)
    restaurants = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    menu_items = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    
    class Meta:
        model = FlashSale
        fields = ['id', 'name', 'description', 'start_time', 'end_time', 'discount_percentage',
                  'restaurants', 'menu_items', 'max_orders', 'current_orders', 'is_active',
                  'is_ongoing', 'created_at', 'updated_at']
        read_only_fields = ['id', 'current_orders', 'is_ongoing', 'created_at', 'updated_at']


class PointsRedemptionSerializer(serializers.Serializer):
    """Serializer for redeeming loyalty points"""
    points = serializers.IntegerField(min_value=1)
    
    def validate_points(self, value):
        user = self.context['request'].user
        try:
            account = user.loyalty_account
            if account.points_balance < value:
                raise serializers.ValidationError("Insufficient points balance.")
            if value < account.program.min_points_redemption:
                raise serializers.ValidationError(
                    f"Minimum redemption is {account.program.min_points_redemption} points."
                )
            return value
        except LoyaltyAccount.DoesNotExist:
            raise serializers.ValidationError("No loyalty account found.")


class ReferralCodeGenerationSerializer(serializers.Serializer):
    """Serializer for generating referral codes"""
    program_id = serializers.UUIDField()
    
    def validate_program_id(self, value):
        try:
            program = ReferralProgram.objects.get(id=value, is_active=True)
            return value
        except ReferralProgram.DoesNotExist:
            raise serializers.ValidationError("Invalid or inactive referral program.")
