from django.contrib import admin
from .models import PaymentMethod, Payment, PaymentRefund, WalletBalance, WalletTransaction


@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    list_display = ['user', 'type', 'is_default', 'is_active', 'created_at']
    list_filter = ['type', 'is_default', 'is_active']
    search_fields = ['user__email', 'user__full_name', 'cardholder_name']


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['order', 'amount', 'status', 'payment_method', 'processed_at']
    list_filter = ['status', 'payment_method__type']
    search_fields = ['order__id', 'transaction_id']
    readonly_fields = ['transaction_id', 'processed_at']


@admin.register(PaymentRefund)
class PaymentRefundAdmin(admin.ModelAdmin):
    list_display = ['payment', 'amount', 'status', 'requested_by', 'processed_at']
    list_filter = ['status']
    search_fields = ['payment__order__id', 'refund_transaction_id']


@admin.register(WalletBalance)
class WalletBalanceAdmin(admin.ModelAdmin):
    list_display = ['user', 'balance', 'currency', 'updated_at']
    search_fields = ['user__email', 'user__full_name']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(WalletTransaction)
class WalletTransactionAdmin(admin.ModelAdmin):
    list_display = ['wallet', 'type', 'amount', 'description', 'created_at']
    list_filter = ['type']
    search_fields = ['wallet__user__email', 'description']
    readonly_fields = ['created_at']
