from django.shortcuts import render
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.filters import SearchFilter, OrderingFilter
from django.utils import timezone
from django.db.models import Q

# Try to import django-filter, fall back to basic filtering if not available
try:
    from django_filters.rest_framework import DjangoFilterBackend
    import django_filters
    HAS_DJANGO_FILTER = True
except ImportError:
    HAS_DJANGO_FILTER = False
    DjangoFilterBackend = None
    django_filters = None

from .models import (
    Promotion, PromotionUsage, Campaign, LoyaltyProgram, 
    CustomerLoyaltyAccount, LoyaltyTransaction
)
from .serializers import (
    PromotionSerializer, PromotionListSerializer, PromotionUsageSerializer,
    CampaignSerializer, LoyaltyProgramSerializer, CustomerLoyaltyAccountSerializer,
    LoyaltyTransactionSerializer, PromotionValidationSerializer
)


# Custom filter for promotions (only if django-filter is available)
if HAS_DJANGO_FILTER:
    class PromotionFilter(django_filters.FilterSet):
        """Custom filter for promotions"""
        status = django_filters.ChoiceFilter(choices=Promotion.PROMOTION_STATUS_CHOICES)
        promotion_type = django_filters.ChoiceFilter(choices=Promotion.PROMOTION_TYPE_CHOICES)
        start_date = django_filters.DateTimeFilter(field_name='start_date', lookup_expr='gte')
        end_date = django_filters.DateTimeFilter(field_name='end_date', lookup_expr='lte')
        is_active = django_filters.BooleanFilter(method='filter_is_active')
        
        class Meta:
            model = Promotion
            fields = ['status', 'promotion_type', 'start_date', 'end_date', 'is_active']
        
        def filter_is_active(self, queryset, name, value):
            """Filter by active promotions (current time within date range and status active)"""
            now = timezone.now()
            if value:
                return queryset.filter(
                    status='ACTIVE',
                    start_date__lte=now,
                    end_date__gte=now
                )
            else:
                return queryset.exclude(
                    status='ACTIVE',
                    start_date__lte=now,
                    end_date__gte=now
                )
else:
    PromotionFilter = None


class PromotionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing promotions
    """
    queryset = Promotion.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    search_fields = ['name', 'code', 'description']
    ordering_fields = ['created_at', 'start_date', 'end_date', 'name', 'status']
    ordering = ['-created_at']

    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'list':
            return PromotionListSerializer
        return PromotionSerializer

    def get_filter_backends(self):
        """Return filter backends based on what's available"""
        backends = [SearchFilter, OrderingFilter]
        if HAS_DJANGO_FILTER and DjangoFilterBackend:
            backends.insert(0, DjangoFilterBackend)
        return backends

    def get_filterset_class(self):
        """Return filterset class if django-filter is available"""
        if HAS_DJANGO_FILTER:
            return PromotionFilter
        return None

    def get_queryset(self):
        """Custom filtering if django-filter is not available"""
        queryset = super().get_queryset()
        
        if not HAS_DJANGO_FILTER:
            # Manual filtering when django-filter is not available
            status_filter = self.request.query_params.get('status', None)
            promotion_type = self.request.query_params.get('promotion_type', None)
            is_active = self.request.query_params.get('is_active', None)
            
            if status_filter:
                queryset = queryset.filter(status=status_filter)
            
            if promotion_type:
                queryset = queryset.filter(promotion_type=promotion_type)
            
            if is_active is not None:
                now = timezone.now()
                if is_active.lower() == 'true':
                    queryset = queryset.filter(
                        status='ACTIVE',
                        start_date__lte=now,
                        end_date__gte=now
                    )
                elif is_active.lower() == 'false':
                    queryset = queryset.exclude(
                        status='ACTIVE',
                        start_date__lte=now,
                        end_date__gte=now
                    )
        
        return queryset

    def perform_create(self, serializer):
        """Set the created_by field to current user"""
        serializer.save(created_by=self.request.user)

    @action(detail=False, methods=['post'])
    def validate_code(self, request):
        """Validate a promotion code"""
        serializer = PromotionValidationSerializer(data=request.data)
        if serializer.is_valid():
            code = serializer.validated_data['code']
            order_amount = serializer.validated_data.get('order_amount', 0)
            
            try:
                promotion = Promotion.objects.get(code=code.upper())
                
                # Check if promotion can be used by user
                if not promotion.can_be_used_by_user(request.user):
                    return Response({
                        'valid': False,
                        'error': 'This promotion cannot be used by your account'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # Calculate discount
                discount_amount = promotion.calculate_discount(order_amount)
                
                return Response({
                    'valid': True,
                    'promotion': PromotionSerializer(promotion).data,
                    'discount_amount': discount_amount
                })
                
            except Promotion.DoesNotExist:
                return Response({
                    'valid': False,
                    'error': 'Invalid promotion code'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def toggle_status(self, request, pk=None):
        """Toggle promotion status between ACTIVE and PAUSED"""
        promotion = self.get_object()
        
        if promotion.status == 'ACTIVE':
            promotion.status = 'PAUSED'
        elif promotion.status in ['DRAFT', 'PAUSED']:
            promotion.status = 'ACTIVE'
        else:
            return Response({
                'error': 'Cannot toggle status for expired or disabled promotions'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        promotion.save()
        return Response(PromotionSerializer(promotion).data)


class PromotionUsageViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing promotion usage history
    """
    queryset = PromotionUsage.objects.all()
    serializer_class = PromotionUsageSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['promotion__name', 'promotion__code', 'user__full_name']
    ordering = ['-created_at']

    def get_queryset(self):
        """Filter by promotion and user if specified"""
        queryset = super().get_queryset()
        promotion_id = self.request.query_params.get('promotion', None)
        user_id = self.request.query_params.get('user', None)
        
        if promotion_id:
            queryset = queryset.filter(promotion_id=promotion_id)
        if user_id:
            queryset = queryset.filter(user_id=user_id)
            
        return queryset


class CampaignViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing marketing campaigns
    """
    queryset = Campaign.objects.all()
    serializer_class = CampaignSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['created_at', 'start_date', 'end_date', 'name']
    ordering = ['-created_at']

    def get_queryset(self):
        """Filter by campaign type and active status"""
        queryset = super().get_queryset()
        campaign_type = self.request.query_params.get('campaign_type', None)
        is_active = self.request.query_params.get('is_active', None)
        
        if campaign_type:
            queryset = queryset.filter(campaign_type=campaign_type)
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
            
        return queryset

    def perform_create(self, serializer):
        """Set the created_by field to current user"""
        serializer.save(created_by=self.request.user)


class LoyaltyProgramViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing loyalty programs
    """
    queryset = LoyaltyProgram.objects.all()
    serializer_class = LoyaltyProgramSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['name', 'description']
    ordering = ['-created_at']


class CustomerLoyaltyAccountViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing customer loyalty accounts
    """
    queryset = CustomerLoyaltyAccount.objects.all()
    serializer_class = CustomerLoyaltyAccountSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['user__full_name', 'user__email']
    ordering_fields = ['total_points_earned', 'total_spent', 'created_at']
    ordering = ['-total_points_earned']

    def get_queryset(self):
        """Filter by tier and loyalty program"""
        queryset = super().get_queryset()
        current_tier = self.request.query_params.get('current_tier', None)
        loyalty_program = self.request.query_params.get('loyalty_program', None)
        
        if current_tier:
            queryset = queryset.filter(current_tier=current_tier)
        if loyalty_program:
            queryset = queryset.filter(loyalty_program_id=loyalty_program)
            
        return queryset


class LoyaltyTransactionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing loyalty transaction history
    """
    queryset = LoyaltyTransaction.objects.all()
    serializer_class = LoyaltyTransactionSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['loyalty_account__user__full_name', 'description']
    ordering = ['-created_at']

    def get_queryset(self):
        """Filter by transaction type and loyalty account"""
        queryset = super().get_queryset()
        transaction_type = self.request.query_params.get('transaction_type', None)
        loyalty_account = self.request.query_params.get('loyalty_account', None)
        
        if transaction_type:
            queryset = queryset.filter(transaction_type=transaction_type)
        if loyalty_account:
            queryset = queryset.filter(loyalty_account_id=loyalty_account)
            
        return queryset
