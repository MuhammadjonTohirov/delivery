from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import transaction
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
import uuid
import string
import random

from .models import (
    PromotionCampaign, Coupon, CouponUsage, LoyaltyProgram, LoyaltyAccount,
    LoyaltyTransaction, ReferralProgram, Referral, FlashSale
)
from .serializers import (
    PromotionCampaignSerializer, CouponSerializer, CouponUsageSerializer,
    CouponValidationSerializer, LoyaltyProgramSerializer, LoyaltyAccountSerializer,
    LoyaltyTransactionSerializer, ReferralProgramSerializer, ReferralSerializer,
    FlashSaleSerializer, PointsRedemptionSerializer, ReferralCodeGenerationSerializer
)
from users.permissions import IsAdminUser, IsCustomer
from drf_spectacular.utils import extend_schema, extend_schema_view


@extend_schema_view(
    list=extend_schema(summary="List promotion campaigns", description="Get all promotion campaigns"),
    retrieve=extend_schema(summary="Get campaign details", description="Get specific campaign details"),
    create=extend_schema(summary="Create campaign", description="Create a new promotion campaign (Admin only)"),
    update=extend_schema(summary="Update campaign", description="Update promotion campaign (Admin only)"),
    partial_update=extend_schema(summary="Partial update campaign", description="Partially update campaign (Admin only)"),
    destroy=extend_schema(summary="Delete campaign", description="Delete promotion campaign (Admin only)"),
)
class PromotionCampaignViewSet(viewsets.ModelViewSet):
    """ViewSet for managing promotion campaigns"""
    serializer_class = PromotionCampaignSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['type', 'status']
    
    def get_queryset(self):
        if self.request.user.is_staff:
            return PromotionCampaign.objects.all()
        # Non-admin users can only see active campaigns
        return PromotionCampaign.objects.filter(status='ACTIVE')
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [permissions.IsAuthenticated, IsAdminUser]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]


@extend_schema_view(
    list=extend_schema(summary="List coupons", description="Get all available coupons"),
    retrieve=extend_schema(summary="Get coupon details", description="Get specific coupon details"),
    create=extend_schema(summary="Create coupon", description="Create a new coupon (Admin only)"),
    update=extend_schema(summary="Update coupon", description="Update coupon (Admin only)"),
    partial_update=extend_schema(summary="Partial update coupon", description="Partially update coupon (Admin only)"),
    destroy=extend_schema(summary="Delete coupon", description="Delete coupon (Admin only)"),
)
class CouponViewSet(viewsets.ModelViewSet):
    """ViewSet for managing coupons"""
    serializer_class = CouponSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['discount_type', 'is_active']
    
    def get_queryset(self):
        if self.request.user.is_staff:
            return Coupon.objects.all()
        # Non-admin users can only see active and valid coupons
        now = timezone.now()
        return Coupon.objects.filter(
            is_active=True,
            start_date__lte=now,
            end_date__gte=now
        )
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [permissions.IsAuthenticated, IsAdminUser]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]
    
    @extend_schema(
        summary="Validate coupon code",
        description="Validate a coupon code and calculate discount"
    )
    @action(detail=False, methods=['post'])
    def validate_code(self, request):
        serializer = CouponValidationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        code = serializer.validated_data['code']
        order_amount = serializer.validated_data.get('order_amount', 0)
        restaurant_id = serializer.validated_data.get('restaurant_id')
        
        try:
            coupon = Coupon.objects.get(code=code)
            
            # Check if user can use this coupon
            user_usage_count = CouponUsage.objects.filter(
                coupon=coupon, 
                user=request.user
            ).count()
            
            if user_usage_count >= coupon.max_uses_per_user:
                return Response(
                    {"error": "You have exceeded the usage limit for this coupon."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Check first order restriction
            if coupon.first_order_only:
                from orders.models import Order
                user_orders = Order.objects.filter(customer=request.user).count()
                if user_orders > 0:
                    return Response(
                        {"error": "This coupon is only valid for first-time orders."},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            # Check minimum order amount
            if coupon.min_order_amount and order_amount < coupon.min_order_amount:
                return Response(
                    {"error": f"Minimum order amount is ${coupon.min_order_amount}."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Check restaurant restriction
            if restaurant_id and coupon.applicable_restaurants.exists():
                if not coupon.applicable_restaurants.filter(id=restaurant_id).exists():
                    return Response(
                        {"error": "This coupon is not valid for the selected restaurant."},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            # Calculate discount
            discount_amount = coupon.calculate_discount(order_amount)
            
            return Response({
                "valid": True,
                "coupon": CouponSerializer(coupon).data,
                "discount_amount": discount_amount
            })
            
        except Coupon.DoesNotExist:
            return Response(
                {"error": "Invalid coupon code."},
                status=status.HTTP_400_BAD_REQUEST
            )


@extend_schema_view(
    list=extend_schema(summary="List coupon usages", description="Get coupon usage history"),
    retrieve=extend_schema(summary="Get usage details", description="Get specific usage details"),
)
class CouponUsageViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing coupon usage history"""
    serializer_class = CouponUsageSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['coupon']
    
    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return CouponUsage.objects.all()
        return CouponUsage.objects.filter(user=user)


@extend_schema_view(
    list=extend_schema(summary="List loyalty programs", description="Get all loyalty programs"),
    retrieve=extend_schema(summary="Get program details", description="Get specific program details"),
    create=extend_schema(summary="Create program", description="Create a new loyalty program (Admin only)"),
    update=extend_schema(summary="Update program", description="Update loyalty program (Admin only)"),
    partial_update=extend_schema(summary="Partial update program", description="Partially update program (Admin only)"),
)
class LoyaltyProgramViewSet(viewsets.ModelViewSet):
    """ViewSet for managing loyalty programs"""
    queryset = LoyaltyProgram.objects.filter(is_active=True)
    serializer_class = LoyaltyProgramSerializer
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [permissions.IsAuthenticated, IsAdminUser]
        else:
            permission_classes = [permissions.AllowAny]
        return [permission() for permission in permission_classes]


@extend_schema_view(
    retrieve=extend_schema(summary="Get loyalty account", description="Get user's loyalty account"),
    update=extend_schema(summary="Update loyalty account", description="Update loyalty account"),
)
class LoyaltyAccountViewSet(viewsets.ModelViewSet):
    """ViewSet for managing user loyalty accounts"""
    serializer_class = LoyaltyAccountSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ['get', 'put', 'patch', 'head', 'options']
    
    def get_queryset(self):
        if self.request.user.is_staff:
            return LoyaltyAccount.objects.all()
        return LoyaltyAccount.objects.filter(user=self.request.user)
    
    def get_object(self):
        # Get or create loyalty account for current user
        try:
            default_program = LoyaltyProgram.objects.filter(is_active=True).first()
            if not default_program:
                # Create a default program if none exists
                default_program = LoyaltyProgram.objects.create(
                    name="Default Loyalty Program",
                    description="Earn points for every order"
                )
            
            account, created = LoyaltyAccount.objects.get_or_create(
                user=self.request.user,
                defaults={'program': default_program}
            )
            return account
        except Exception as e:
            return None
    
    @extend_schema(
        summary="Redeem points",
        description="Redeem loyalty points for credit"
    )
    @action(detail=False, methods=['post'])
    def redeem_points(self, request):
        serializer = PointsRedemptionSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        
        points = serializer.validated_data['points']
        
        try:
            with transaction.atomic():
                account = request.user.loyalty_account
                program = account.program
                
                # Calculate credit value
                credit_value = points * program.points_redemption_value
                
                # Deduct points
                old_balance = account.points_balance
                account.points_balance -= points
                account.total_points_redeemed += points
                account.save()
                
                # Create transaction record
                LoyaltyTransaction.objects.create(
                    account=account,
                    type='REDEEMED',
                    points=-points,
                    description=f"Redeemed {points} points for ${credit_value} credit",
                    balance_before=old_balance,
                    balance_after=account.points_balance
                )
                
                # Add credit to wallet (if wallet app is available)
                try:
                    from payments.models import WalletBalance, WalletTransaction
                    wallet, created = WalletBalance.objects.get_or_create(
                        user=request.user,
                        defaults={'balance': 0}
                    )
                    old_wallet_balance = wallet.balance
                    wallet.balance += credit_value
                    wallet.save()
                    
                    WalletTransaction.objects.create(
                        wallet=wallet,
                        type='CREDIT',
                        amount=credit_value,
                        description=f"Loyalty points redemption ({points} points)",
                        balance_before=old_wallet_balance,
                        balance_after=wallet.balance
                    )
                except ImportError:
                    pass  # Wallet functionality not available
                
                return Response({
                    "success": True,
                    "points_redeemed": points,
                    "credit_value": credit_value,
                    "remaining_balance": account.points_balance
                })
                
        except LoyaltyAccount.DoesNotExist:
            return Response(
                {"error": "No loyalty account found."},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": f"Redemption failed: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @extend_schema(
        summary="Get points history",
        description="Get user's loyalty points transaction history"
    )
    @action(detail=False, methods=['get'])
    def points_history(self, request):
        try:
            account = request.user.loyalty_account
            transactions = account.transactions.all().order_by('-created_at')
            serializer = LoyaltyTransactionSerializer(transactions, many=True)
            return Response(serializer.data)
        except LoyaltyAccount.DoesNotExist:
            return Response([])


@extend_schema_view(
    list=extend_schema(summary="List referral programs", description="Get all referral programs"),
    retrieve=extend_schema(summary="Get program details", description="Get specific program details"),
)
class ReferralProgramViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing referral programs"""
    queryset = ReferralProgram.objects.filter(is_active=True)
    serializer_class = ReferralProgramSerializer
    permission_classes = [permissions.IsAuthenticated]


@extend_schema_view(
    list=extend_schema(summary="List referrals", description="Get user's referral history"),
    retrieve=extend_schema(summary="Get referral details", description="Get specific referral details"),
)
class ReferralViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for managing referrals"""
    serializer_class = ReferralSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Referral.objects.all()
        return Referral.objects.filter(referrer=user)
    
    @extend_schema(
        summary="Generate referral code",
        description="Generate a new referral code for a program"
    )
    @action(detail=False, methods=['post'])
    def generate_code(self, request):
        serializer = ReferralCodeGenerationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        program_id = serializer.validated_data['program_id']
        
        try:
            program = ReferralProgram.objects.get(id=program_id)
            
            # Generate unique referral code
            while True:
                code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
                if not Referral.objects.filter(referral_code=code).exists():
                    break
            
            # Check if user already has an active referral for this program
            existing_referral = Referral.objects.filter(
                referrer=request.user,
                program=program,
                status='PENDING'
            ).first()
            
            if existing_referral:
                return Response({
                    "referral_code": existing_referral.referral_code,
                    "message": "You already have an active referral code for this program."
                })
            
            # Create new referral (without referee initially)
            referral = Referral.objects.create(
                referrer=request.user,
                program=program,
                referral_code=code,
                referee=request.user  # Temporary, will be updated when someone uses the code
            )
            
            return Response({
                "referral_code": code,
                "program": program.name,
                "referrer_reward": f"{program.referrer_reward_value} {program.referrer_reward_type}",
                "referee_reward": f"{program.referee_reward_value} {program.referee_reward_type}"
            })
            
        except ReferralProgram.DoesNotExist:
            return Response(
                {"error": "Referral program not found."},
                status=status.HTTP_404_NOT_FOUND
            )


@extend_schema_view(
    list=extend_schema(summary="List flash sales", description="Get all flash sales"),
    retrieve=extend_schema(summary="Get flash sale details", description="Get specific flash sale details"),
    create=extend_schema(summary="Create flash sale", description="Create a new flash sale (Admin only)"),
    update=extend_schema(summary="Update flash sale", description="Update flash sale (Admin only)"),
    partial_update=extend_schema(summary="Partial update flash sale", description="Partially update flash sale (Admin only)"),
)
class FlashSaleViewSet(viewsets.ModelViewSet):
    """ViewSet for managing flash sales"""
    serializer_class = FlashSaleSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['is_active']
    
    def get_queryset(self):
        if self.request.user.is_staff:
            return FlashSale.objects.all()
        # Non-admin users can only see active and ongoing flash sales
        now = timezone.now()
        return FlashSale.objects.filter(
            is_active=True,
            start_time__lte=now,
            end_time__gte=now
        )
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [permissions.IsAuthenticated, IsAdminUser]
        else:
            permission_classes = [permissions.AllowAny]
        return [permission() for permission in permission_classes]
    
    @extend_schema(
        summary="Get active flash sales",
        description="Get all currently active flash sales"
    )
    @action(detail=False, methods=['get'])
    def active(self, request):
        now = timezone.now()
        active_sales = FlashSale.objects.filter(
            is_active=True,
            start_time__lte=now,
            end_time__gte=now
        )
        
        # Filter by max_orders if specified
        valid_sales = []
        for sale in active_sales:
            if sale.max_orders is None or sale.current_orders < sale.max_orders:
                valid_sales.append(sale)
        
        serializer = self.get_serializer(valid_sales, many=True)
        return Response(serializer.data)
