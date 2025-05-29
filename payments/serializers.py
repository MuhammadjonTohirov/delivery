from rest_framework import serializers
from .models import PaymentMethod, Payment, PaymentRefund, WalletBalance, WalletTransaction


class PaymentMethodSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentMethod
        fields = ['id', 'type', 'is_default', 'is_active', 'card_last_four', 
                  'card_brand', 'cardholder_name', 'wallet_provider', 'created_at']
        read_only_fields = ['id', 'created_at']
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        
        # If this is set as default, make all other payment methods non-default
        if validated_data.get('is_default', False):
            PaymentMethod.objects.filter(
                user=validated_data['user'], 
                is_default=True
            ).update(is_default=False)
        
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        # If this is set as default, make all other payment methods non-default
        if validated_data.get('is_default', False):
            PaymentMethod.objects.filter(
                user=instance.user, 
                is_default=True
            ).exclude(id=instance.id).update(is_default=False)
        
        return super().update(instance, validated_data)


class PaymentSerializer(serializers.ModelSerializer):
    order_id = serializers.UUIDField(source='order.id', read_only=True)
    payment_method_display = serializers.CharField(source='payment_method.__str__', read_only=True)
    remaining_refundable_amount = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    
    class Meta:
        model = Payment
        fields = ['id', 'order', 'order_id', 'payment_method', 'payment_method_display',
                  'amount', 'currency', 'status', 'transaction_id', 'failure_reason',
                  'refunded_amount', 'remaining_refundable_amount', 'processed_at', 'created_at']
        read_only_fields = ['id', 'order_id', 'payment_method_display', 'remaining_refundable_amount',
                           'processed_at', 'created_at', 'transaction_id', 'refunded_amount']


class PaymentRefundSerializer(serializers.ModelSerializer):
    requested_by_name = serializers.CharField(source='requested_by.full_name', read_only=True)
    
    class Meta:
        model = PaymentRefund
        fields = ['id', 'payment', 'amount', 'reason', 'status', 'refund_transaction_id',
                  'requested_by', 'requested_by_name', 'processed_at', 'created_at']
        read_only_fields = ['id', 'refund_transaction_id', 'requested_by', 'requested_by_name',
                           'processed_at', 'created_at']
    
    def create(self, validated_data):
        validated_data['requested_by'] = self.context['request'].user
        return super().create(validated_data)


class WalletBalanceSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.full_name', read_only=True)
    
    class Meta:
        model = WalletBalance
        fields = ['id', 'user', 'user_name', 'balance', 'currency', 'created_at', 'updated_at']
        read_only_fields = ['id', 'user', 'user_name', 'created_at', 'updated_at']


class WalletTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = WalletTransaction
        fields = ['id', 'wallet', 'type', 'amount', 'description', 'reference_id',
                  'balance_before', 'balance_after', 'created_at']
        read_only_fields = ['id', 'balance_before', 'balance_after', 'created_at']


class PaymentCreateSerializer(serializers.Serializer):
    """Serializer for creating payment for an order"""
    order_id = serializers.UUIDField()
    payment_method_id = serializers.UUIDField()
    
    def validate_order_id(self, value):
        from orders.models import Order
        try:
            order = Order.objects.get(id=value)
            if order.customer != self.context['request'].user:
                raise serializers.ValidationError("You can only pay for your own orders.")
            if hasattr(order, 'payment'):
                raise serializers.ValidationError("Payment already exists for this order.")
            return value
        except Order.DoesNotExist:
            raise serializers.ValidationError("Order not found.")
    
    def validate_payment_method_id(self, value):
        try:
            payment_method = PaymentMethod.objects.get(
                id=value, 
                user=self.context['request'].user,
                is_active=True
            )
            return value
        except PaymentMethod.DoesNotExist:
            raise serializers.ValidationError("Payment method not found or inactive.")


class WalletTopUpSerializer(serializers.Serializer):
    """Serializer for wallet top-up"""
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=1)
    payment_method_id = serializers.UUIDField()
    
    def validate_payment_method_id(self, value):
        try:
            payment_method = PaymentMethod.objects.get(
                id=value, 
                user=self.context['request'].user,
                is_active=True
            )
            if payment_method.type == 'CASH':
                raise serializers.ValidationError("Cannot use cash for wallet top-up.")
            return value
        except PaymentMethod.DoesNotExist:
            raise serializers.ValidationError("Payment method not found or inactive.")
