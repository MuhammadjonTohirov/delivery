from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import transaction
from django.utils import timezone
from decimal import Decimal
import uuid

from .models import PaymentMethod, Payment, PaymentRefund, WalletBalance, WalletTransaction
from .serializers import (
    PaymentMethodSerializer, PaymentSerializer, PaymentRefundSerializer,
    WalletBalanceSerializer, WalletTransactionSerializer, PaymentCreateSerializer,
    WalletTopUpSerializer
)
from orders.models import Order
from users.permissions import IsCustomer, IsAdminUser
from drf_spectacular.utils import extend_schema, extend_schema_view


class PaymentMethodPermission(permissions.BasePermission):
    """Custom permission for payment methods"""
    def has_object_permission(self, request, view, obj):
        # Users can only access their own payment methods
        if request.user.is_staff:
            return True
        return obj.user == request.user


@extend_schema_view(
    list=extend_schema(summary="List payment methods", description="Get user's payment methods"),
    retrieve=extend_schema(summary="Get payment method", description="Get specific payment method details"),
    create=extend_schema(summary="Add payment method", description="Add a new payment method"),
    update=extend_schema(summary="Update payment method", description="Update payment method details"),
    partial_update=extend_schema(summary="Partial update payment method", description="Partially update payment method"),
    destroy=extend_schema(summary="Delete payment method", description="Delete a payment method"),
)
class PaymentMethodViewSet(viewsets.ModelViewSet):
    """ViewSet for managing user payment methods"""
    serializer_class = PaymentMethodSerializer
    permission_classes = [permissions.IsAuthenticated, PaymentMethodPermission]
    
    def get_queryset(self):
        if self.request.user.is_staff:
            return PaymentMethod.objects.all()
        return PaymentMethod.objects.filter(user=self.request.user, is_active=True)
    
    @extend_schema(
        summary="Set as default payment method",
        description="Set this payment method as the default"
    )
    @action(detail=True, methods=['post'])
    def set_default(self, request, pk=None):
        payment_method = self.get_object()
        
        # Remove default from all other payment methods
        PaymentMethod.objects.filter(
            user=request.user, 
            is_default=True
        ).update(is_default=False)
        
        # Set this one as default
        payment_method.is_default = True
        payment_method.save()
        
        serializer = self.get_serializer(payment_method)
        return Response(serializer.data)


@extend_schema_view(
    list=extend_schema(summary="List payments", description="Get user's payment history"),
    retrieve=extend_schema(summary="Get payment details", description="Get specific payment details"),
)
class PaymentViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing payment history"""
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Payment.objects.all().select_related('order', 'payment_method')
        elif user.role == 'CUSTOMER':
            return Payment.objects.filter(
                order__customer=user
            ).select_related('order', 'payment_method')
        elif user.role == 'RESTAURANT':
            if hasattr(user, 'restaurant'):
                return Payment.objects.filter(
                    order__restaurant=user.restaurant
                ).select_related('order', 'payment_method')
        return Payment.objects.none()
    
    @extend_schema(
        summary="Create payment for order",
        description="Process payment for an order"
    )
    @action(detail=False, methods=['post'], permission_classes=[permissions.IsAuthenticated, IsCustomer])
    def pay_order(self, request):
        serializer = PaymentCreateSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        
        order_id = serializer.validated_data['order_id']
        payment_method_id = serializer.validated_data['payment_method_id']
        
        try:
            with transaction.atomic():
                order = Order.objects.get(id=order_id)
                payment_method = PaymentMethod.objects.get(id=payment_method_id)
                
                # Create payment record
                payment = Payment.objects.create(
                    order=order,
                    payment_method=payment_method,
                    amount=order.total_price,
                    status='PENDING',
                    transaction_id=str(uuid.uuid4())  # In production, use real payment gateway
                )
                
                # Simulate payment processing
                if payment_method.type == 'CASH':
                    payment.status = 'PENDING'  # Cash on delivery remains pending
                else:
                    # Simulate successful payment processing
                    payment.status = 'COMPLETED'
                    payment.processed_at = timezone.now()
                    
                    # If using wallet, deduct balance
                    if payment_method.type == 'DIGITAL_WALLET':
                        wallet, created = WalletBalance.objects.get_or_create(
                            user=request.user,
                            defaults={'balance': 0}
                        )
                        if wallet.balance >= order.total_price:
                            # Deduct from wallet
                            old_balance = wallet.balance
                            wallet.balance -= order.total_price
                            wallet.save()
                            
                            # Create wallet transaction
                            WalletTransaction.objects.create(
                                wallet=wallet,
                                type='DEBIT',
                                amount=order.total_price,
                                description=f"Payment for order #{order.id}",
                                reference_id=str(order.id),
                                balance_before=old_balance,
                                balance_after=wallet.balance
                            )
                        else:
                            payment.status = 'FAILED'
                            payment.failure_reason = 'Insufficient wallet balance'
                
                payment.save()
                
                # Update order status if payment successful
                if payment.status == 'COMPLETED':
                    order.update_status('CONFIRMED', request.user, "Payment completed successfully")
                
                serializer = PaymentSerializer(payment)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
                
        except Exception as e:
            return Response(
                {"error": f"Payment processing failed: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @extend_schema(
        summary="Request refund",
        description="Request a refund for a payment"
    )
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def request_refund(self, request, pk=None):
        payment = self.get_object()
        
        # Check if refund is possible
        if payment.status not in ['COMPLETED']:
            return Response(
                {"error": "Can only refund completed payments"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if payment.remaining_refundable_amount <= 0:
            return Response(
                {"error": "No refundable amount remaining"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check user permission
        if not (request.user.is_staff or payment.order.customer == request.user):
            return Response(
                {"error": "You don't have permission to refund this payment"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        refund_data = {
            'payment': payment.id,
            'amount': request.data.get('amount', payment.remaining_refundable_amount),
            'reason': request.data.get('reason', 'Customer requested refund')
        }
        
        serializer = PaymentRefundSerializer(data=refund_data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        refund = serializer.save()
        
        # Process refund (simplified)
        with transaction.atomic():
            refund.status = 'COMPLETED'
            refund.processed_at = timezone.now()
            refund.refund_transaction_id = str(uuid.uuid4())
            refund.save()
            
            # Update payment
            payment.refunded_amount += refund.amount
            if payment.refunded_amount >= payment.amount:
                payment.status = 'REFUNDED'
            else:
                payment.status = 'PARTIALLY_REFUNDED'
            payment.save()
            
            # If wallet payment, credit back to wallet
            if payment.payment_method.type == 'DIGITAL_WALLET':
                wallet = payment.order.customer.wallet
                old_balance = wallet.balance
                wallet.balance += refund.amount
                wallet.save()
                
                WalletTransaction.objects.create(
                    wallet=wallet,
                    type='CREDIT',
                    amount=refund.amount,
                    description=f"Refund for order #{payment.order.id}",
                    reference_id=str(payment.order.id),
                    balance_before=old_balance,
                    balance_after=wallet.balance
                )
        
        return Response(PaymentRefundSerializer(refund).data, status=status.HTTP_201_CREATED)


@extend_schema_view(
    retrieve=extend_schema(summary="Get wallet balance", description="Get user's wallet balance"),
    update=extend_schema(summary="Update wallet", description="Update wallet details"),
)
class WalletViewSet(viewsets.ModelViewSet):
    """ViewSet for wallet management"""
    serializer_class = WalletBalanceSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ['get', 'put', 'patch', 'head', 'options']
    
    def get_queryset(self):
        if self.request.user.is_staff:
            return WalletBalance.objects.all()
        return WalletBalance.objects.filter(user=self.request.user)
    
    def get_object(self):
        # Get or create wallet for current user
        wallet, created = WalletBalance.objects.get_or_create(
            user=self.request.user,
            defaults={'balance': 0}
        )
        return wallet
    
    @extend_schema(
        summary="Top up wallet",
        description="Add money to wallet using a payment method"
    )
    @action(detail=False, methods=['post'])
    def top_up(self, request):
        serializer = WalletTopUpSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        
        amount = serializer.validated_data['amount']
        payment_method_id = serializer.validated_data['payment_method_id']
        
        try:
            with transaction.atomic():
                payment_method = PaymentMethod.objects.get(id=payment_method_id)
                wallet, created = WalletBalance.objects.get_or_create(
                    user=request.user,
                    defaults={'balance': 0}
                )
                
                # Simulate successful top-up (in production, integrate with payment gateway)
                old_balance = wallet.balance
                wallet.balance += amount
                wallet.save()
                
                # Create transaction record
                WalletTransaction.objects.create(
                    wallet=wallet,
                    type='CREDIT',
                    amount=amount,
                    description=f"Wallet top-up via {payment_method}",
                    balance_before=old_balance,
                    balance_after=wallet.balance
                )
                
                serializer = WalletBalanceSerializer(wallet)
                return Response(serializer.data)
                
        except Exception as e:
            return Response(
                {"error": f"Top-up failed: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @extend_schema(
        summary="Get wallet transactions",
        description="Get user's wallet transaction history"
    )
    @action(detail=False, methods=['get'])
    def transactions(self, request):
        wallet, created = WalletBalance.objects.get_or_create(
            user=request.user,
            defaults={'balance': 0}
        )
        
        transactions = wallet.transactions.all().order_by('-created_at')
        serializer = WalletTransactionSerializer(transactions, many=True)
        return Response(serializer.data)


@extend_schema_view(
    list=extend_schema(summary="List payment refunds", description="Get payment refund history"),
    retrieve=extend_schema(summary="Get refund details", description="Get specific refund details"),
)
class PaymentRefundViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing refund history"""
    serializer_class = PaymentRefundSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return PaymentRefund.objects.all()
        elif user.role == 'CUSTOMER':
            return PaymentRefund.objects.filter(payment__order__customer=user)
        elif user.role == 'RESTAURANT':
            if hasattr(user, 'restaurant'):
                return PaymentRefund.objects.filter(payment__order__restaurant=user.restaurant)
        return PaymentRefund.objects.none()
