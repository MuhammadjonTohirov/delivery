from rest_framework import serializers
from django.utils import timezone
from .models import (
    Promotion, PromotionUsage, Campaign, LoyaltyProgram, 
    CustomerLoyaltyAccount, LoyaltyTransaction
)


class PromotionSerializer(serializers.ModelSerializer):
    """Full serializer for Promotion CRUD operations"""
    created_by_name = serializers.CharField(source='created_by.full_name', read_only=True)
    is_currently_active = serializers.BooleanField(source='is_active', read_only=True)
    applicable_restaurants = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    applicable_menu_items = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    
    class Meta:
        model = Promotion
        fields = [
            'id', 'name', 'code', 'description', 'promotion_type', 'status',
            'discount_percentage', 'discount_amount', 'minimum_order_amount',
            'maximum_discount_amount', 'usage_limit', 'usage_limit_per_user',
            'current_usage_count', 'start_date', 'end_date',
            'applicable_to_new_users_only', 'applicable_restaurants',
            'applicable_menu_items', 'created_by', 'created_by_name',
            'is_currently_active', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'current_usage_count', 'created_by', 'created_by_name',
            'is_currently_active', 'created_at', 'updated_at'
        ]

    def validate_code(self, value):
        """Ensure promotion code is unique"""
        code = value.upper()
        if self.instance and self.instance.code == code:
            return code
        
        if Promotion.objects.filter(code=code).exists():
            raise serializers.ValidationError("A promotion with this code already exists.")
        return code

    def validate(self, data):
        """Validate promotion data"""
        promotion_type = data.get('promotion_type')
        
        # Validate discount values based on type
        if promotion_type == 'PERCENTAGE':
            if not data.get('discount_percentage'):
                raise serializers.ValidationError({
                    'discount_percentage': 'This field is required for percentage discounts.'
                })
            if data.get('discount_percentage', 0) <= 0 or data.get('discount_percentage', 0) > 100:
                raise serializers.ValidationError({
                    'discount_percentage': 'Percentage must be between 0 and 100.'
                })
        
        elif promotion_type == 'FIXED_AMOUNT':
            if not data.get('discount_amount'):
                raise serializers.ValidationError({
                    'discount_amount': 'This field is required for fixed amount discounts.'
                })
            if data.get('discount_amount', 0) <= 0:
                raise serializers.ValidationError({
                    'discount_amount': 'Discount amount must be greater than 0.'
                })
        
        # Validate date range
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        
        if start_date and end_date and start_date >= end_date:
            raise serializers.ValidationError({
                'end_date': 'End date must be after start date.'
            })
        
        return data

    def create(self, validated_data):
        """Create promotion with uppercase code"""
        validated_data['code'] = validated_data['code'].upper()
        return super().create(validated_data)

    def update(self, instance, validated_data):
        """Update promotion with uppercase code"""
        if 'code' in validated_data:
            validated_data['code'] = validated_data['code'].upper()
        return super().update(instance, validated_data)


class PromotionListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for promotion list view"""
    created_by_name = serializers.CharField(source='created_by.full_name', read_only=True)
    is_currently_active = serializers.BooleanField(source='is_active', read_only=True)
    usage_percentage = serializers.SerializerMethodField()
    
    class Meta:
        model = Promotion
        fields = [
            'id', 'name', 'code', 'promotion_type', 'status',
            'discount_percentage', 'discount_amount', 'start_date', 'end_date',
            'current_usage_count', 'usage_limit', 'usage_percentage',
            'created_by_name', 'is_currently_active', 'created_at'
        ]

    def get_usage_percentage(self, obj):
        """Calculate usage percentage"""
        if obj.usage_limit and obj.usage_limit > 0:
            return round((obj.current_usage_count / obj.usage_limit) * 100, 1)
        return None


class PromotionUsageSerializer(serializers.ModelSerializer):
    """Serializer for promotion usage tracking"""
    promotion_name = serializers.CharField(source='promotion.name', read_only=True)
    promotion_code = serializers.CharField(source='promotion.code', read_only=True)
    user_name = serializers.CharField(source='user.full_name', read_only=True)
    order_id = serializers.UUIDField(source='order.id', read_only=True)
    
    class Meta:
        model = PromotionUsage
        fields = [
            'id', 'promotion', 'promotion_name', 'promotion_code',
            'user', 'user_name', 'order', 'order_id',
            'discount_amount', 'original_order_amount', 'final_order_amount',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class PromotionValidationSerializer(serializers.Serializer):
    """Serializer for validating promotion codes"""
    code = serializers.CharField(max_length=50)
    order_amount = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    restaurant_id = serializers.UUIDField(required=False)

    def validate_code(self, value):
        """Convert code to uppercase"""
        return value.upper()


class CampaignSerializer(serializers.ModelSerializer):
    """Serializer for marketing campaigns"""
    created_by_name = serializers.CharField(source='created_by.full_name', read_only=True)
    is_currently_active = serializers.BooleanField(read_only=True)
    promotions = PromotionListSerializer(many=True, read_only=True)
    budget_utilization_percentage = serializers.FloatField(source='budget_utilization', read_only=True)
    
    class Meta:
        model = Campaign
        fields = [
            'id', 'name', 'description', 'campaign_type', 'is_active',
            'start_date', 'end_date', 'promotions', 'target_user_roles',
            'target_cities', 'budget', 'spent_amount', 'budget_utilization_percentage',
            'impressions', 'clicks', 'conversions', 'created_by',
            'created_by_name', 'is_currently_active', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'spent_amount', 'budget_utilization_percentage',
            'impressions', 'clicks', 'conversions', 'created_by',
            'created_by_name', 'is_currently_active', 'created_at', 'updated_at'
        ]


class LoyaltyProgramSerializer(serializers.ModelSerializer):
    """Serializer for loyalty programs"""
    
    class Meta:
        model = LoyaltyProgram
        fields = [
            'id', 'name', 'description', 'points_per_dollar', 'points_redemption_value',
            'bronze_tier_threshold', 'silver_tier_threshold', 'gold_tier_threshold',
            'platinum_tier_threshold', 'is_active', 'points_expiry_days',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class CustomerLoyaltyAccountSerializer(serializers.ModelSerializer):
    """Serializer for customer loyalty accounts"""
    user_name = serializers.CharField(source='user.full_name', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)
    program_name = serializers.CharField(source='loyalty_program.name', read_only=True)
    
    class Meta:
        model = CustomerLoyaltyAccount
        fields = [
            'id', 'user', 'user_name', 'user_email', 'loyalty_program',
            'program_name', 'total_points_earned', 'total_points_redeemed',
            'current_points_balance', 'current_tier', 'tier_progress',
            'total_orders', 'total_spent', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'user_name', 'user_email', 'program_name',
            'total_points_earned', 'total_points_redeemed', 'current_points_balance',
            'tier_progress', 'total_orders', 'total_spent', 'created_at', 'updated_at'
        ]


class LoyaltyTransactionSerializer(serializers.ModelSerializer):
    """Serializer for loyalty transactions"""
    account_user_name = serializers.CharField(source='loyalty_account.user.full_name', read_only=True)
    
    class Meta:
        model = LoyaltyTransaction
        fields = [
            'id', 'loyalty_account', 'account_user_name', 'transaction_type',
            'points', 'order', 'promotion', 'description', 'expiry_date',
            'created_at'
        ]
        read_only_fields = ['id', 'account_user_name', 'created_at']
