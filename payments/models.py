from django.db import models
from django.conf import settings
from core.models import TimeStampedModel
from orders.models import Order
import uuid


class PaymentMethod(TimeStampedModel):
    PAYMENT_TYPE_CHOICES = (
        ('CASH', 'Cash on Delivery'),
        ('CARD', 'Credit/Debit Card'),
        ('DIGITAL_WALLET', 'Digital Wallet'),
        ('BANK_TRANSFER', 'Bank Transfer'),
    )
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='payment_methods')
    type = models.CharField(max_length=20, choices=PAYMENT_TYPE_CHOICES)
    is_default = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    
    # Card details (encrypted in production)
    card_last_four = models.CharField(max_length=4, blank=True, null=True)
    card_brand = models.CharField(max_length=20, blank=True, null=True)  # Visa, Mastercard, etc.
    cardholder_name = models.CharField(max_length=100, blank=True, null=True)
    
    # Digital wallet details
    wallet_provider = models.CharField(max_length=50, blank=True, null=True)  # PayPal, Apple Pay, etc.
    wallet_account_id = models.CharField(max_length=100, blank=True, null=True)
    
    class Meta:
        ordering = ['-is_default', '-created_at']
    
    def __str__(self):
        if self.type == 'CARD' and self.card_last_four:
            return f"{self.card_brand} ending in {self.card_last_four}"
        elif self.type == 'DIGITAL_WALLET' and self.wallet_provider:
            return f"{self.wallet_provider}"
        return f"{self.get_type_display()}"


class Payment(TimeStampedModel):
    PAYMENT_STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('PROCESSING', 'Processing'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
        ('CANCELLED', 'Cancelled'),
        ('REFUNDED', 'Refunded'),
        ('PARTIALLY_REFUNDED', 'Partially Refunded'),
    )
    
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='payment')
    payment_method = models.ForeignKey(PaymentMethod, on_delete=models.SET_NULL, null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='PENDING')
    
    # Payment gateway fields
    transaction_id = models.CharField(max_length=100, unique=True, null=True, blank=True)
    gateway_response = models.JSONField(default=dict, blank=True)
    
    # Failure details
    failure_reason = models.TextField(blank=True, null=True)
    
    # Refund tracking
    refunded_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    processed_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"Payment for Order {self.order.id} - {self.status}"
    
    @property
    def remaining_refundable_amount(self):
        return self.amount - self.refunded_amount


class PaymentRefund(TimeStampedModel):
    REFUND_STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('PROCESSING', 'Processing'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
    )
    
    payment = models.ForeignKey(Payment, on_delete=models.CASCADE, related_name='refunds')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=REFUND_STATUS_CHOICES, default='PENDING')
    
    # Gateway details
    refund_transaction_id = models.CharField(max_length=100, unique=True, null=True, blank=True)
    gateway_response = models.JSONField(default=dict, blank=True)
    
    requested_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"Refund {self.amount} for Payment {self.payment.id}"


class PaymentTransaction(TimeStampedModel):
    TRANSACTION_TYPE_CHOICES = (
        ('CHARGE', 'Charge'),
        ('REFUND', 'Refund'),
        ('ADJUSTMENT', 'Adjustment'),
    )
    
    payment = models.ForeignKey(Payment, on_delete=models.CASCADE, related_name='transactions')
    type = models.CharField(max_length=20, choices=TRANSACTION_TYPE_CHOICES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.CharField(max_length=255)
    
    # Gateway integration
    gateway_transaction_id = models.CharField(max_length=100, unique=True)
    gateway_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    processed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    
    def __str__(self):
        return f"{self.type} - {self.amount} for Payment {self.payment.id}"


class WalletBalance(TimeStampedModel):
    """User wallet for storing credits/balance"""
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='wallet')
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    currency = models.CharField(max_length=3, default='USD')
    
    def __str__(self):
        return f"Wallet for {self.user.full_name} - {self.balance} {self.currency}"


class WalletTransaction(TimeStampedModel):
    TRANSACTION_TYPE_CHOICES = (
        ('CREDIT', 'Credit'),
        ('DEBIT', 'Debit'),
    )
    
    wallet = models.ForeignKey(WalletBalance, on_delete=models.CASCADE, related_name='transactions')
    type = models.CharField(max_length=10, choices=TRANSACTION_TYPE_CHOICES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.CharField(max_length=255)
    reference_id = models.CharField(max_length=100, blank=True, null=True)  # Order ID, etc.
    
    # Balance tracking
    balance_before = models.DecimalField(max_digits=10, decimal_places=2)
    balance_after = models.DecimalField(max_digits=10, decimal_places=2)
    
    def __str__(self):
        return f"{self.type} {self.amount} - {self.description}"
