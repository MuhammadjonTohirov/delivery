from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from core.models import TimeStampedModel
import uuid


class Promotion(TimeStampedModel):
    """
    Promotion and discount codes
    """
    PROMOTION_TYPE_CHOICES = (
        ('PERCENTAGE', 'Percentage Discount'),
        ('FIXED_AMOUNT', 'Fixed Amount Discount'),
        ('FREE_DELIVERY', 'Free Delivery'),
        ('BOGO', 'Buy One Get One'),
        ('MINIMUM_ORDER', 'Minimum Order Discount'),
    )
    
    PROMOTION_STATUS_CHOICES = (
        ('DRAFT', 'Draft'),
        ('ACTIVE', 'Active'),
        ('PAUSED', 'Paused'),
        ('EXPIRED', 'Expired'),
        ('DISABLED', 'Disabled'),
    )
    
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    
    # Promotion settings
    promotion_type = models.CharField(max_length=20, choices=PROMOTION_TYPE_CHOICES)
    status = models.CharField(max_length=10, choices=PROMOTION_STATUS_CHOICES, default='DRAFT')
    
    # Discount values
    discount_percentage = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Conditions
    minimum_order_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    maximum_discount_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Usage limits
    usage_limit = models.IntegerField(null=True, blank=True, help_text="Total number of times this promotion can be used")
    usage_limit_per_user = models.IntegerField(null=True, blank=True, help_text="Number of times each user can use this promotion")
    current_usage_count = models.IntegerField(default=0)
    
    # Date restrictions
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    
    # Target restrictions
    applicable_to_new_users_only = models.BooleanField(default=False)
    applicable_restaurants = models.ManyToManyField('restaurants.Restaurant', blank=True)
    applicable_menu_items = models.ManyToManyField('restaurants.MenuItem', blank=True)
    
    # Admin fields
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['status', 'start_date', 'end_date']),
            models.Index(fields=['promotion_type']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.code})"
    
    @property
    def is_active(self):
        """Check if promotion is currently active"""
        from django.utils import timezone
        now = timezone.now()
        return (
            self.status == 'ACTIVE' and
            self.start_date <= now <= self.end_date and
            (self.usage_limit is None or self.current_usage_count < self.usage_limit)
        )
    
    def can_be_used_by_user(self, user):
        """Check if promotion can be used by a specific user"""
        if not self.is_active:
            return False
        
        # Check new user restriction
        if self.applicable_to_new_users_only:
            from orders.models import Order
            if Order.objects.filter(customer=user).exists():
                return False
        
        # Check per-user usage limit
        if self.usage_limit_per_user:
            user_usage_count = PromotionUsage.objects.filter(
                promotion=self,
                user=user
            ).count()
            if user_usage_count >= self.usage_limit_per_user:
                return False
        
        return True
    
    def calculate_discount(self, order_amount, restaurant=None):
        """Calculate discount amount for given order"""
        if not self.is_active:
            return 0
        
        # Check minimum order amount
        if self.minimum_order_amount and order_amount < self.minimum_order_amount:
            return 0
        
        # Calculate discount based on type
        if self.promotion_type == 'PERCENTAGE':
            discount = order_amount * (self.discount_percentage / 100)
            if self.maximum_discount_amount:
                discount = min(discount, self.maximum_discount_amount)
            return discount
        
        elif self.promotion_type == 'FIXED_AMOUNT':
            return min(self.discount_amount, order_amount)
        
        elif self.promotion_type == 'FREE_DELIVERY':
            # Return delivery fee amount (would need to be calculated)
            return 5.00  # Default delivery fee
        
        return 0


class PromotionUsage(TimeStampedModel):
    """
    Track promotion usage by users
    """
    promotion = models.ForeignKey(Promotion, on_delete=models.CASCADE, related_name='usages')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='promotion_usages')
    order = models.ForeignKey('orders.Order', on_delete=models.CASCADE, related_name='promotion_usages')
    
    # Usage details
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2)
    original_order_amount = models.DecimalField(max_digits=10, decimal_places=2)
    final_order_amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['promotion', 'user']),
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['order']),
        ]
    
    def __str__(self):
        return f"{self.user.full_name} used {self.promotion.code} - ${self.discount_amount} off"


class Campaign(TimeStampedModel):
    """
    Marketing campaigns that can contain multiple promotions
    """
    CAMPAIGN_TYPE_CHOICES = (
        ('SEASONAL', 'Seasonal'),
        ('HOLIDAY', 'Holiday'),
        ('LAUNCH', 'New Launch'),
        ('RETENTION', 'Customer Retention'),
        ('ACQUISITION', 'Customer Acquisition'),
        ('PARTNERSHIP', 'Partnership'),
    )
    
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    campaign_type = models.CharField(max_length=20, choices=CAMPAIGN_TYPE_CHOICES)
    
    # Campaign settings
    is_active = models.BooleanField(default=False)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    
    # Associated promotions
    promotions = models.ManyToManyField(Promotion, related_name='campaigns', blank=True)
    
    # Target audience
    target_user_roles = models.CharField(max_length=100, blank=True, help_text="Comma-separated user roles")
    target_cities = models.CharField(max_length=200, blank=True, help_text="Comma-separated city names")
    
    # Budget and limits
    budget = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    spent_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Tracking
    impressions = models.IntegerField(default=0)
    clicks = models.IntegerField(default=0)
    conversions = models.IntegerField(default=0)
    
    # Admin fields
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['campaign_type', 'is_active']),
            models.Index(fields=['start_date', 'end_date']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.campaign_type})"
    
    @property
    def is_currently_active(self):
        """Check if campaign is currently running"""
        from django.utils import timezone
        now = timezone.now()
        return self.is_active and self.start_date <= now <= self.end_date
    
    @property
    def budget_utilization(self):
        """Calculate budget utilization percentage"""
        if not self.budget:
            return 0
        return (self.spent_amount / self.budget) * 100


class LoyaltyProgram(TimeStampedModel):
    """
    Customer loyalty program
    """
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    
    # Points system
    points_per_dollar = models.DecimalField(max_digits=5, decimal_places=2, default=1)
    points_redemption_value = models.DecimalField(max_digits=5, decimal_places=4, default=0.01)  # $0.01 per point
    
    # Tier system
    bronze_tier_threshold = models.IntegerField(default=0)
    silver_tier_threshold = models.IntegerField(default=500)
    gold_tier_threshold = models.IntegerField(default=1000)
    platinum_tier_threshold = models.IntegerField(default=2000)
    
    # Settings
    is_active = models.BooleanField(default=True)
    points_expiry_days = models.IntegerField(null=True, blank=True, help_text="Days after which points expire")
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name


class CustomerLoyaltyAccount(TimeStampedModel):
    """
    Individual customer loyalty account
    """
    TIER_CHOICES = (
        ('BRONZE', 'Bronze'),
        ('SILVER', 'Silver'),
        ('GOLD', 'Gold'),
        ('PLATINUM', 'Platinum'),
    )
    
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='loyalty_account')
    loyalty_program = models.ForeignKey(LoyaltyProgram, on_delete=models.CASCADE, related_name='customer_accounts')
    
    # Points balance
    total_points_earned = models.IntegerField(default=0)
    total_points_redeemed = models.IntegerField(default=0)
    current_points_balance = models.IntegerField(default=0)
    
    # Tier information
    current_tier = models.CharField(max_length=10, choices=TIER_CHOICES, default='BRONZE')
    tier_progress = models.IntegerField(default=0, help_text="Points towards next tier")
    
    # Statistics
    total_orders = models.IntegerField(default=0)
    total_spent = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    class Meta:
        ordering = ['-total_points_earned']
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['current_tier']),
        ]
    
    def __str__(self):
        return f"{self.user.full_name} - {self.current_tier} ({self.current_points_balance} points)"
    
    def add_points(self, points, order=None):
        """Add points to account"""
        self.total_points_earned += points
        self.current_points_balance += points
        self.save()
        
        # Create transaction record
        LoyaltyTransaction.objects.create(
            loyalty_account=self,
            transaction_type='EARNED',
            points=points,
            order=order,
            description=f"Points earned from order #{order.id}" if order else "Points added"
        )
        
        # Update tier if necessary
        self.update_tier()
    
    def redeem_points(self, points, order=None, description="Points redeemed"):
        """Redeem points from account"""
        if points > self.current_points_balance:
            raise ValueError("Insufficient points balance")
        
        self.total_points_redeemed += points
        self.current_points_balance -= points
        self.save()
        
        # Create transaction record
        LoyaltyTransaction.objects.create(
            loyalty_account=self,
            transaction_type='REDEEMED',
            points=-points,
            order=order,
            description=description
        )
    
    def update_tier(self):
        """Update customer tier based on total points earned"""
        program = self.loyalty_program
        
        if self.total_points_earned >= program.platinum_tier_threshold:
            self.current_tier = 'PLATINUM'
        elif self.total_points_earned >= program.gold_tier_threshold:
            self.current_tier = 'GOLD'
        elif self.total_points_earned >= program.silver_tier_threshold:
            self.current_tier = 'SILVER'
        else:
            self.current_tier = 'BRONZE'
        
        self.save()


class LoyaltyTransaction(TimeStampedModel):
    """
    Individual loyalty point transactions
    """
    TRANSACTION_TYPE_CHOICES = (
        ('EARNED', 'Points Earned'),
        ('REDEEMED', 'Points Redeemed'),
        ('EXPIRED', 'Points Expired'),
        ('BONUS', 'Bonus Points'),
        ('ADJUSTMENT', 'Manual Adjustment'),
    )
    
    loyalty_account = models.ForeignKey(CustomerLoyaltyAccount, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(max_length=15, choices=TRANSACTION_TYPE_CHOICES)
    points = models.IntegerField()  # Positive for earned, negative for redeemed
    
    # Related objects
    order = models.ForeignKey('orders.Order', on_delete=models.SET_NULL, null=True, blank=True)
    promotion = models.ForeignKey(Promotion, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Additional details
    description = models.CharField(max_length=200)
    expiry_date = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['loyalty_account', 'transaction_type']),
            models.Index(fields=['transaction_type', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.loyalty_account.user.full_name} - {self.transaction_type} {self.points} points"
