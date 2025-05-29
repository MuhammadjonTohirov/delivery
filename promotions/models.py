from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from core.models import TimeStampedModel
from restaurants.models import Restaurant, MenuItem
from decimal import Decimal
import uuid


class PromotionCampaign(TimeStampedModel):
    CAMPAIGN_TYPE_CHOICES = (
        ('DISCOUNT', 'Discount'),
        ('CASHBACK', 'Cashback'),
        ('FREE_DELIVERY', 'Free Delivery'),
        ('BOGO', 'Buy One Get One'),
    )
    
    STATUS_CHOICES = (
        ('DRAFT', 'Draft'),
        ('ACTIVE', 'Active'),
        ('PAUSED', 'Paused'),
        ('EXPIRED', 'Expired'),
    )
    
    name = models.CharField(max_length=100)
    description = models.TextField()
    type = models.CharField(max_length=20, choices=CAMPAIGN_TYPE_CHOICES)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='DRAFT')
    
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    
    # Usage limits
    max_uses_total = models.PositiveIntegerField(null=True, blank=True)
    max_uses_per_user = models.PositiveIntegerField(default=1)
    current_uses = models.PositiveIntegerField(default=0)
    
    # Restrictions
    restaurants = models.ManyToManyField(Restaurant, blank=True, related_name='campaigns')
    menu_items = models.ManyToManyField(MenuItem, blank=True, related_name='campaigns')
    min_order_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Targeting
    target_user_roles = models.JSONField(default=list, blank=True)  # ['CUSTOMER', 'DRIVER']
    target_new_users_only = models.BooleanField(default=False)
    
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    
    def __str__(self):
        return f"{self.name} ({self.type})"
    
    @property
    def is_active(self):
        from django.utils import timezone
        now = timezone.now()
        return (
            self.status == 'ACTIVE' and
            self.start_date <= now <= self.end_date and
            (self.max_uses_total is None or self.current_uses < self.max_uses_total)
        )


class Coupon(TimeStampedModel):
    DISCOUNT_TYPE_CHOICES = (
        ('PERCENTAGE', 'Percentage'),
        ('FIXED_AMOUNT', 'Fixed Amount'),
        ('FREE_DELIVERY', 'Free Delivery'),
    )
    
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    
    discount_type = models.CharField(max_length=15, choices=DISCOUNT_TYPE_CHOICES)
    discount_value = models.DecimalField(max_digits=10, decimal_places=2)
    max_discount_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    min_order_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    
    # Usage tracking
    max_uses = models.PositiveIntegerField(null=True, blank=True)
    max_uses_per_user = models.PositiveIntegerField(default=1)
    current_uses = models.PositiveIntegerField(default=0)
    
    is_active = models.BooleanField(default=True)
    
    # Restrictions
    applicable_restaurants = models.ManyToManyField(Restaurant, blank=True, related_name='coupons')
    applicable_menu_items = models.ManyToManyField(MenuItem, blank=True, related_name='coupons')
    
    # Targeting
    first_order_only = models.BooleanField(default=False)
    
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    
    def __str__(self):
        return f"{self.code} - {self.name}"
    
    def calculate_discount(self, order_amount):
        """Calculate discount amount for given order amount"""
        if self.discount_type == 'PERCENTAGE':
            discount = order_amount * (self.discount_value / 100)
            if self.max_discount_amount:
                discount = min(discount, self.max_discount_amount)
        elif self.discount_type == 'FIXED_AMOUNT':
            discount = self.discount_value
        elif self.discount_type == 'FREE_DELIVERY':
            # This would be handled differently, returning delivery fee as discount
            discount = Decimal('0')  # Placeholder
        
        return min(discount, order_amount)
    
    @property
    def is_valid(self):
        from django.utils import timezone
        now = timezone.now()
        return (
            self.is_active and
            self.start_date <= now <= self.end_date and
            (self.max_uses is None or self.current_uses < self.max_uses)
        )


class CouponUsage(TimeStampedModel):
    coupon = models.ForeignKey(Coupon, on_delete=models.CASCADE, related_name='usages')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='coupon_usages')
    order = models.ForeignKey('orders.Order', on_delete=models.CASCADE, related_name='coupon_usage')
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    class Meta:
        unique_together = ('coupon', 'order')
    
    def __str__(self):
        return f"{self.coupon.code} used by {self.user.full_name} - Order {self.order.id}"


class LoyaltyProgram(TimeStampedModel):
    name = models.CharField(max_length=100)
    description = models.TextField()
    
    # Points configuration
    points_per_dollar = models.DecimalField(max_digits=5, decimal_places=2, default=1)
    points_redemption_value = models.DecimalField(max_digits=5, decimal_places=4, default=0.01)  # $0.01 per point
    min_points_redemption = models.PositiveIntegerField(default=100)
    
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.name


class LoyaltyAccount(TimeStampedModel):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='loyalty_account')
    program = models.ForeignKey(LoyaltyProgram, on_delete=models.CASCADE, related_name='accounts')
    points_balance = models.PositiveIntegerField(default=0)
    total_points_earned = models.PositiveIntegerField(default=0)
    total_points_redeemed = models.PositiveIntegerField(default=0)
    
    def __str__(self):
        return f"{self.user.full_name} - {self.points_balance} points"


class LoyaltyTransaction(TimeStampedModel):
    TRANSACTION_TYPE_CHOICES = (
        ('EARNED', 'Points Earned'),
        ('REDEEMED', 'Points Redeemed'),
        ('EXPIRED', 'Points Expired'),
        ('ADJUSTMENT', 'Manual Adjustment'),
    )
    
    account = models.ForeignKey(LoyaltyAccount, on_delete=models.CASCADE, related_name='transactions')
    type = models.CharField(max_length=15, choices=TRANSACTION_TYPE_CHOICES)
    points = models.IntegerField()  # Can be negative for redemptions
    description = models.CharField(max_length=255)
    reference_order = models.ForeignKey('orders.Order', on_delete=models.SET_NULL, null=True, blank=True)
    
    # Balance tracking
    balance_before = models.PositiveIntegerField()
    balance_after = models.PositiveIntegerField()
    
    def __str__(self):
        return f"{self.type}: {self.points} points for {self.account.user.full_name}"


class ReferralProgram(TimeStampedModel):
    name = models.CharField(max_length=100)
    description = models.TextField()
    
    # Rewards
    referrer_reward_type = models.CharField(max_length=20, default='POINTS')  # POINTS, CREDIT, COUPON
    referrer_reward_value = models.DecimalField(max_digits=10, decimal_places=2)
    
    referee_reward_type = models.CharField(max_length=20, default='POINTS')
    referee_reward_value = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Conditions
    min_referee_orders = models.PositiveIntegerField(default=1)
    min_referee_order_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.name


class Referral(TimeStampedModel):
    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    )
    
    referrer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='referrals_made')
    referee = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='referrals_received')
    program = models.ForeignKey(ReferralProgram, on_delete=models.CASCADE, related_name='referrals')
    referral_code = models.CharField(max_length=20, unique=True)
    
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='PENDING')
    
    # Tracking
    referee_orders_count = models.PositiveIntegerField(default=0)
    referee_total_spent = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    completed_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.referrer.full_name} referred {self.referee.full_name}"


class FlashSale(TimeStampedModel):
    name = models.CharField(max_length=100)
    description = models.TextField()
    
    # Timing
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    
    # Discount
    discount_percentage = models.DecimalField(
        max_digits=5, 
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    
    # Targeting
    restaurants = models.ManyToManyField(Restaurant, blank=True, related_name='flash_sales')
    menu_items = models.ManyToManyField(MenuItem, blank=True, related_name='flash_sales')
    
    # Limits
    max_orders = models.PositiveIntegerField(null=True, blank=True)
    current_orders = models.PositiveIntegerField(default=0)
    
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.name} - {self.discount_percentage}% off"
    
    @property
    def is_ongoing(self):
        from django.utils import timezone
        now = timezone.now()
        return (
            self.is_active and
            self.start_time <= now <= self.end_time and
            (self.max_orders is None or self.current_orders < self.max_orders)
        )
