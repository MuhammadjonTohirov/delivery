from django.db import models
from django.conf import settings
from core.models import TimeStampedModel
import uuid


class Payment(TimeStampedModel):
    """
    Payment records for orders
    """
    PAYMENT_STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('PROCESSING', 'Processing'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
        ('CANCELLED', 'Cancelled'),
        ('REFUNDED', 'Refunded'),
    )
    
    PAYMENT_METHOD_CHOICES = (
        ('CARD', 'Credit/Debit Card'),
        ('CASH', 'Cash on Delivery'),
        ('WALLET', 'Digital Wallet'),
        ('BANK_TRANSFER', 'Bank Transfer'),
    )
    
    order = models.OneToOneField('orders.Order', on_delete=models.CASCADE, related_name='payment')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='payments')
    
    # Payment details
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='UZS')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='PENDING')
    
    # External payment provider details
    provider = models.CharField(max_length=50, null=True, blank=True)  # e.g., 'stripe', 'paypal'
    provider_transaction_id = models.CharField(max_length=200, null=True, blank=True)
    provider_payment_intent_id = models.CharField(max_length=200, null=True, blank=True)
    
    # Payment metadata
    metadata = models.JSONField(default=dict, blank=True)
    
    # Timestamps
    processed_at = models.DateTimeField(null=True, blank=True)
    failed_at = models.DateTimeField(null=True, blank=True)
    refunded_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['provider_transaction_id']),
        ]
    
    def __str__(self):
        return f"Payment {self.id} - {self.amount} {self.currency} - {self.status}"


class PaymentMethod(TimeStampedModel):
    """
    Saved payment methods for users
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='payment_methods')
    
    # Payment method details
    method_type = models.CharField(max_length=20, choices=Payment.PAYMENT_METHOD_CHOICES)
    is_default = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    
    # Card details (if applicable)
    card_last_four = models.CharField(max_length=4, null=True, blank=True)
    card_brand = models.CharField(max_length=20, null=True, blank=True)  # visa, mastercard, etc.
    card_exp_month = models.IntegerField(null=True, blank=True)
    card_exp_year = models.IntegerField(null=True, blank=True)
    cardholder_name = models.CharField(max_length=100, null=True, blank=True)
    
    # External provider details
    provider = models.CharField(max_length=50, null=True, blank=True)
    provider_payment_method_id = models.CharField(max_length=200, null=True, blank=True)
    
    # Billing address
    billing_address = models.TextField(null=True, blank=True)
    
    class Meta:
        ordering = ['-is_default', '-created_at']
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['provider_payment_method_id']),
        ]
    
    def __str__(self):
        if self.method_type == 'CARD' and self.card_last_four:
            return f"{self.card_brand} ****{self.card_last_four}"
        return f"{self.get_method_type_display()}"
    
    def save(self, *args, **kwargs):
        # Ensure only one default payment method per user
        if self.is_default:
            PaymentMethod.objects.filter(user=self.user, is_default=True).update(is_default=False)
        super().save(*args, **kwargs)


class Refund(TimeStampedModel):
    """
    Refund records
    """
    REFUND_STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('PROCESSING', 'Processing'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
        ('CANCELLED', 'Cancelled'),
    )
    
    REFUND_REASON_CHOICES = (
        ('CUSTOMER_REQUEST', 'Customer Request'),
        ('ORDER_CANCELLED', 'Order Cancelled'),
        ('QUALITY_ISSUE', 'Quality Issue'),
        ('DELIVERY_FAILED', 'Delivery Failed'),
        ('RESTAURANT_CANCELLED', 'Restaurant Cancelled'),
        ('ADMIN_REFUND', 'Administrative Refund'),
    )
    
    payment = models.ForeignKey(Payment, on_delete=models.CASCADE, related_name='refunds')
    order = models.ForeignKey('orders.Order', on_delete=models.CASCADE, related_name='refunds')
    
    # Refund details
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    reason = models.CharField(max_length=30, choices=REFUND_REASON_CHOICES)
    status = models.CharField(max_length=20, choices=REFUND_STATUS_CHOICES, default='PENDING')
    
    # External provider details
    provider_refund_id = models.CharField(max_length=200, null=True, blank=True)
    
    # Admin details
    processed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    notes = models.TextField(null=True, blank=True)
    
    # Timestamps
    processed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['payment', 'status']),
            models.Index(fields=['status', 'created_at']),
        ]
    
    def __str__(self):
        return f"Refund {self.id} - {self.amount} for Payment {self.payment.id}"


class PaymentTransaction(TimeStampedModel):
    """
    Detailed payment transaction log
    """
    TRANSACTION_TYPE_CHOICES = (
        ('CHARGE', 'Charge'),
        ('REFUND', 'Refund'),
        ('PARTIAL_REFUND', 'Partial Refund'),
        ('CHARGEBACK', 'Chargeback'),
        ('DISPUTE', 'Dispute'),
    )
    
    payment = models.ForeignKey(Payment, on_delete=models.CASCADE, related_name='transactions')
    
    # Transaction details
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPE_CHOICES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='UZS')
    
    # External provider details
    provider_transaction_id = models.CharField(max_length=200)
    provider_response = models.JSONField(default=dict, blank=True)
    
    # Status
    is_successful = models.BooleanField(default=False)
    error_message = models.TextField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['payment', 'transaction_type']),
            models.Index(fields=['provider_transaction_id']),
        ]
    
    def __str__(self):
        return f"{self.transaction_type} - {self.amount} {self.currency}"


class PaymentWebhook(models.Model):
    """
    Log of payment provider webhooks
    """
    provider = models.CharField(max_length=50)
    event_type = models.CharField(max_length=100)
    event_id = models.CharField(max_length=200, unique=True)
    
    # Webhook data
    payload = models.JSONField()
    headers = models.JSONField(default=dict, blank=True)
    
    # Processing status
    processed = models.BooleanField(default=False)
    processed_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(null=True, blank=True)
    
    # Related payment (if applicable)
    payment = models.ForeignKey(Payment, on_delete=models.SET_NULL, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['provider', 'event_type']),
            models.Index(fields=['processed', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.provider} - {self.event_type} - {self.event_id}"
