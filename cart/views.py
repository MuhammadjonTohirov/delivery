from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend

from .models import Cart, CartItem, SavedCart, CartPromotion, CartAbandonment
from .serializers import (
    CartSerializer, CartItemSerializer, SavedCartSerializer, CartPromotionSerializer,
    CartAbandonmentSerializer, AddToCartSerializer, UpdateCartItemSerializer,
    SetDeliveryAddressSerializer, SaveCartSerializer, ApplyPromotionSerializer,
    CartCheckoutSerializer, CartSummarySerializer
)
from restaurants.models import MenuItem
from users.permissions import IsCustomer
from drf_spectacular.utils import extend_schema, extend_schema_view


class CartPermission(permissions.BasePermission):
    """
    Custom permission for cart operations:
    - Users can only access their own cart
    - Admins can view all carts
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        if request.user.is_staff:
            return True
        return obj.user == request.user


@extend_schema_view(
    retrieve=extend_schema(summary="Get cart", description="Get user's current cart"),
    update=extend_schema(summary="Update cart", description="Update cart details"),
    partial_update=extend_schema(summary="Partial update cart", description="Partially update cart"),
)
class CartViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing shopping cart
    """
    serializer_class = CartSerializer
    permission_classes = [CartPermission]
    http_method_names = ['get', 'put', 'patch', 'head', 'options']  # No POST or DELETE
    
    def get_queryset(self):
        # Handle schema generation case
        if getattr(self, 'swagger_fake_view', False):
            return Cart.objects.none()
            
        user = self.request.user
        
        if user.is_staff:
            return Cart.objects.all()
        
        return Cart.objects.filter(user=user)
    
    def get_object(self):
        """
        Get or create cart for the current user
        """
        user = self.request.user
        cart, created = Cart.objects.get_or_create(user=user)
        return cart
    
    @extend_schema(
        summary="Add item to cart",
        description="Add a menu item to the user's cart"
    )
    @action(detail=False, methods=['post'])
    def add_item(self, request):
        """
        Add item to cart
        """
        serializer = AddToCartSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        data = serializer.validated_data
        menu_item = get_object_or_404(MenuItem, id=data['menu_item_id'])
        
        # Get or create cart
        cart, created = Cart.objects.get_or_create(user=request.user)
        
        # Add item to cart
        cart_item = cart.add_item(
            menu_item=menu_item,
            quantity=data['quantity'],
            special_instructions=data.get('special_instructions', '')
        )
        
        # Return updated cart
        cart_serializer = CartSerializer(cart)
        return Response(cart_serializer.data, status=status.HTTP_200_OK)
    
    @extend_schema(
        summary="Update cart item",
        description="Update quantity or instructions for a cart item"
    )
    @action(detail=False, methods=['patch'], url_path='items/(?P<item_id>[^/.]+)')
    def update_item(self, request, item_id=None):
        """
        Update cart item quantity or instructions
        """
        serializer = UpdateCartItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        cart = self.get_object()
        
        try:
            cart_item = cart.items.get(id=item_id)
        except CartItem.DoesNotExist:
            return Response(
                {"error": "Cart item not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        data = serializer.validated_data
        
        if data['quantity'] == 0:
            cart_item.delete()
        else:
            cart_item.quantity = data['quantity']
            if 'special_instructions' in data:
                cart_item.special_instructions = data['special_instructions']
            cart_item.save()
        
        # Return updated cart
        cart_serializer = CartSerializer(cart)
        return Response(cart_serializer.data)
    
    @extend_schema(
        summary="Remove item from cart",
        description="Remove a specific item from cart"
    )
    @action(detail=False, methods=['delete'], url_path='items/(?P<item_id>[^/.]+)')
    def remove_item(self, request, item_id=None):
        """
        Remove item from cart
        """
        cart = self.get_object()
        
        try:
            cart_item = cart.items.get(id=item_id)
            cart_item.delete()
        except CartItem.DoesNotExist:
            return Response(
                {"error": "Cart item not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Return updated cart
        cart_serializer = CartSerializer(cart)
        return Response(cart_serializer.data)
    
    @extend_schema(
        summary="Clear cart",
        description="Remove all items from cart"
    )
    @action(detail=False, methods=['post'])
    def clear(self, request):
        """
        Clear all items from cart
        """
        cart = self.get_object()
        cart.clear()
        
        cart_serializer = CartSerializer(cart)
        return Response(cart_serializer.data)
    
    @extend_schema(
        summary="Set delivery address",
        description="Set delivery address for the cart"
    )
    @action(detail=False, methods=['post'])
    def set_delivery_address(self, request):
        """
        Set delivery address for cart
        """
        serializer = SetDeliveryAddressSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        cart = self.get_object()
        data = serializer.validated_data
        
        cart.delivery_address = data['delivery_address']
        cart.delivery_lat = data.get('delivery_lat')
        cart.delivery_lng = data.get('delivery_lng')
        cart.delivery_instructions = data.get('delivery_instructions', '')
        cart.save()
        
        cart_serializer = CartSerializer(cart)
        return Response(cart_serializer.data)
    
    @extend_schema(
        summary="Get cart summary",
        description="Get cart summary with totals and fees"
    )
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """
        Get cart summary with all totals
        """
        cart = self.get_object()
        
        # Calculate summary data
        summary_data = {
            'total_items': cart.total_items,
            'subtotal': cart.subtotal,
            'delivery_fee': cart.estimated_delivery_fee,
            'tax_amount': 0,  # Tax calculation would be implemented based on location
            'discount_amount': 0,  # Would calculate from applied promotions
            'total': cart.total,
            'restaurant_name': cart.restaurant.name if cart.restaurant else '',
            'estimated_delivery_time': 35  # Would calculate based on distance and restaurant prep time
        }
        
        serializer = CartSummarySerializer(summary_data)
        return Response(serializer.data)
    
    @extend_schema(
        summary="Validate cart for checkout",
        description="Validate cart items and availability before checkout"
    )
    @action(detail=False, methods=['post'])
    def validate_checkout(self, request):
        """
        Validate cart for checkout
        """
        cart = self.get_object()
        
        if not cart.items.exists():
            return Response(
                {"error": "Cart is empty"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check item availability
        unavailable_items = []
        for item in cart.items.all():
            if not item.menu_item.is_available:
                unavailable_items.append(item.menu_item.name)
        
        if unavailable_items:
            return Response(
                {
                    "error": "Some items are no longer available",
                    "unavailable_items": unavailable_items
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check restaurant is open
        if cart.restaurant and not cart.restaurant.is_open:
            return Response(
                {"error": "Restaurant is currently closed"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check delivery address
        if not cart.delivery_address:
            return Response(
                {"error": "Delivery address is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return Response({"message": "Cart is valid for checkout"})


@extend_schema_view(
    list=extend_schema(summary="List saved carts", description="List user's saved carts"),
    retrieve=extend_schema(summary="Get saved cart", description="Get a specific saved cart"),
    create=extend_schema(summary="Save current cart", description="Save current cart for later"),
    destroy=extend_schema(summary="Delete saved cart", description="Delete a saved cart"),
)
class SavedCartViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing saved carts
    """
    serializer_class = SavedCartSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        # Handle schema generation case
        if getattr(self, 'swagger_fake_view', False):
            return SavedCart.objects.none()
            
        return SavedCart.objects.filter(user=self.request.user)
    
    @extend_schema(
        summary="Save current cart",
        description="Save the user's current cart with a name"
    )
    @action(detail=False, methods=['post'])
    def save_current_cart(self, request):
        """
        Save current cart as a saved cart
        """
        serializer = SaveCartSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Get current cart
        try:
            cart = Cart.objects.get(user=request.user)
        except Cart.DoesNotExist:
            return Response(
                {"error": "No active cart found"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not cart.items.exists():
            return Response(
                {"error": "Cart is empty"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create saved cart
        saved_cart = SavedCart.create_from_cart(
            user=request.user,
            cart=cart,
            name=serializer.validated_data['name']
        )
        
        if serializer.validated_data.get('is_favorite'):
            saved_cart.is_favorite = True
            saved_cart.save()
        
        saved_cart_serializer = SavedCartSerializer(saved_cart)
        return Response(saved_cart_serializer.data, status=status.HTTP_201_CREATED)
    
    @extend_schema(
        summary="Restore saved cart",
        description="Restore a saved cart to current cart"
    )
    @action(detail=True, methods=['post'])
    def restore(self, request, pk=None):
        """
        Restore saved cart to current cart
        """
        saved_cart = self.get_object()
        cart = saved_cart.restore_to_cart()
        
        # Update usage statistics
        saved_cart.times_reordered += 1
        saved_cart.last_ordered = timezone.now()
        saved_cart.save()
        
        cart_serializer = CartSerializer(cart)
        return Response(cart_serializer.data)


class CartAbandonmentViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for cart abandonment analytics (Admin only)
    """
    serializer_class = CartAbandonmentSerializer
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['recovered', 'abandonment_stage', 'restaurant']
    
    def get_queryset(self):
        return CartAbandonment.objects.all().order_by('-abandoned_at')
    
    @extend_schema(
        summary="Get abandonment statistics",
        description="Get cart abandonment statistics for analytics"
    )
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """
        Get cart abandonment statistics
        """
        from django.db.models import Count, Avg, Sum
        from datetime import timedelta
        
        end_date = timezone.now()
        start_date = end_date - timedelta(days=30)
        
        # Get statistics
        total_abandonments = CartAbandonment.objects.filter(
            abandoned_at__gte=start_date
        ).count()
        
        recovered_count = CartAbandonment.objects.filter(
            abandoned_at__gte=start_date,
            recovered=True
        ).count()
        
        recovery_rate = (recovered_count / total_abandonments * 100) if total_abandonments > 0 else 0
        
        # Abandonment by stage
        by_stage = CartAbandonment.objects.filter(
            abandoned_at__gte=start_date
        ).values('abandonment_stage').annotate(
            count=Count('id')
        ).order_by('-count')
        
        # Average cart value
        avg_cart_value = CartAbandonment.objects.filter(
            abandoned_at__gte=start_date
        ).aggregate(Avg('cart_value'))['cart_value__avg'] or 0
        
        return Response({
            'total_abandonments': total_abandonments,
            'recovered_count': recovered_count,
            'recovery_rate': round(recovery_rate, 2),
            'average_cart_value': round(avg_cart_value, 2),
            'abandonments_by_stage': list(by_stage),
            'period_days': 30
        })
