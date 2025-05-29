from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import transaction
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend

from .models import (
    Cart, CartItem, MenuItemCustomization, CustomerFavorite, 
    SavedCart, QuickReorder, RecentOrder
)
from .serializers import (
    CartSerializer, CartItemSerializer, AddToCartSerializer, UpdateCartItemSerializer,
    ApplyCouponSerializer, CustomerFavoriteSerializer, SavedCartSerializer,
    QuickReorderSerializer, RecentOrderSerializer, CheckoutSerializer,
    CartRestaurantChangeSerializer, MenuItemCustomizationSerializer
)
from restaurants.models import MenuItem, Restaurant
from users.permissions import IsCustomer
from drf_spectacular.utils import extend_schema, extend_schema_view


@extend_schema_view(
    retrieve=extend_schema(summary="Get user's cart", description="Get current user's shopping cart"),
    update=extend_schema(summary="Update cart", description="Update cart details"),
    partial_update=extend_schema(summary="Partial update cart", description="Partially update cart"),
)
class CartViewSet(viewsets.ModelViewSet):
    """ViewSet for managing shopping cart"""
    serializer_class = CartSerializer
    permission_classes = [permissions.IsAuthenticated, IsCustomer]
    http_method_names = ['get', 'put', 'patch', 'head', 'options']
    
    def get_queryset(self):
        return Cart.objects.filter(user=self.request.user)
    
    def get_object(self):
        # Get or create cart for current user
        cart, created = Cart.objects.get_or_create(
            user=self.request.user,
            defaults={'is_active': True}
        )
        return cart
    
    @extend_schema(
        summary="Add item to cart",
        description="Add a menu item to the shopping cart"
    )
    @action(detail=False, methods=['post'])
    def add_item(self, request):
        serializer = AddToCartSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        menu_item_id = serializer.validated_data['menu_item_id']
        quantity = serializer.validated_data['quantity']
        special_instructions = serializer.validated_data.get('special_instructions', '')
        customizations = serializer.validated_data.get('customizations', [])
        
        try:
            with transaction.atomic():
                menu_item = MenuItem.objects.get(id=menu_item_id)
                cart = self.get_object()
                
                # Check if cart is empty or from same restaurant
                if cart.restaurant and cart.restaurant != menu_item.restaurant:
                    return Response(
                        {
                            "error": "Cannot add items from different restaurants. Clear cart first.",
                            "current_restaurant": cart.restaurant.name,
                            "new_restaurant": menu_item.restaurant.name
                        },
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                # Set restaurant if cart is empty
                if not cart.restaurant:
                    cart.restaurant = menu_item.restaurant
                    cart.save()
                
                # Check if item already exists in cart
                cart_item, created = CartItem.objects.get_or_create(
                    cart=cart,
                    menu_item=menu_item,
                    defaults={
                        'quantity': quantity,
                        'special_instructions': special_instructions
                    }
                )
                
                if not created:
                    # Update existing item
                    cart_item.quantity += quantity
                    cart_item.special_instructions = special_instructions
                    cart_item.save()
                
                # Handle customizations
                if customizations:
                    cart_item.customizations.all().delete()  # Clear existing
                    
                    for custom_data in customizations:
                        customization = MenuItemCustomization.objects.get(
                            id=custom_data['customization_id']
                        )
                        
                        # Calculate additional price for customizations
                        additional_price = 0
                        for option_id in custom_data['selected_options']:
                            option = customization.options.get(id=option_id)
                            additional_price += option.additional_price
                        
                        cart_item.customizations.create(
                            customization=customization,
                            selected_options=custom_data['selected_options'],
                            additional_price=additional_price
                        )
                
                # Recalculate cart totals
                cart.calculate_totals()
                
                serializer = CartSerializer(cart)
                return Response(serializer.data)
                
        except MenuItem.DoesNotExist:
            return Response(
                {"error": "Menu item not found."},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": f"Failed to add item to cart: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @extend_schema(
        summary="Update cart item",
        description="Update quantity or instructions for a cart item"
    )
    @action(detail=False, methods=['put'], url_path='items/(?P<item_id>[^/.]+)')
    def update_item(self, request, item_id=None):
        try:
            cart = self.get_object()
            cart_item = cart.items.get(id=item_id)
            
            serializer = UpdateCartItemSerializer(cart_item, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            
            cart.calculate_totals()
            
            return Response(CartItemSerializer(cart_item).data)
            
        except CartItem.DoesNotExist:
            return Response(
                {"error": "Cart item not found."},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @extend_schema(
        summary="Remove item from cart",
        description="Remove a specific item from the cart"
    )
    @action(detail=False, methods=['delete'], url_path='items/(?P<item_id>[^/.]+)')
    def remove_item(self, request, item_id=None):
        try:
            cart = self.get_object()
            cart_item = cart.items.get(id=item_id)
            cart_item.delete()
            
            # If cart is empty, clear restaurant
            if not cart.items.exists():
                cart.restaurant = None
            
            cart.calculate_totals()
            
            return Response({"message": "Item removed from cart."})
            
        except CartItem.DoesNotExist:
            return Response(
                {"error": "Cart item not found."},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @extend_schema(
        summary="Clear cart",
        description="Remove all items from the cart"
    )
    @action(detail=False, methods=['post'])
    def clear(self, request):
        cart = self.get_object()
        cart.clear()
        
        return Response({"message": "Cart cleared successfully."})
    
    @extend_schema(
        summary="Apply coupon",
        description="Apply a coupon code to the cart"
    )
    @action(detail=False, methods=['post'])
    def apply_coupon(self, request):
        serializer = ApplyCouponSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        coupon_code = serializer.validated_data['coupon_code']
        
        try:
            from promotions.models import Coupon, CouponUsage
            
            cart = self.get_object()
            coupon = Coupon.objects.get(code=coupon_code)
            
            # Validate coupon for this user and cart
            user_usage_count = CouponUsage.objects.filter(
                coupon=coupon, 
                user=request.user
            ).count()
            
            if user_usage_count >= coupon.max_uses_per_user:
                return Response(
                    {"error": "You have exceeded the usage limit for this coupon."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Check minimum order amount
            if coupon.min_order_amount and cart.subtotal < coupon.min_order_amount:
                return Response(
                    {"error": f"Minimum order amount is ${coupon.min_order_amount}."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Check restaurant restriction
            if coupon.applicable_restaurants.exists():
                if not coupon.applicable_restaurants.filter(id=cart.restaurant.id).exists():
                    return Response(
                        {"error": "This coupon is not valid for the selected restaurant."},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            # Apply coupon
            cart.applied_coupon = coupon
            cart.calculate_totals()
            
            discount_amount = coupon.calculate_discount(cart.subtotal)
            
            return Response({
                "message": "Coupon applied successfully.",
                "discount_amount": discount_amount,
                "cart": CartSerializer(cart).data
            })
            
        except Coupon.DoesNotExist:
            return Response(
                {"error": "Invalid coupon code."},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @extend_schema(
        summary="Remove coupon",
        description="Remove applied coupon from cart"
    )
    @action(detail=False, methods=['post'])
    def remove_coupon(self, request):
        cart = self.get_object()
        cart.applied_coupon = None
        cart.calculate_totals()
        
        return Response({
            "message": "Coupon removed successfully.",
            "cart": CartSerializer(cart).data
        })
    
    @extend_schema(
        summary="Change restaurant",
        description="Change restaurant (clears current cart)"
    )
    @action(detail=False, methods=['post'])
    def change_restaurant(self, request):
        serializer = CartRestaurantChangeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        restaurant_id = serializer.validated_data['restaurant_id']
        restaurant = Restaurant.objects.get(id=restaurant_id)
        
        cart = self.get_object()
        cart.clear()  # This clears all items and resets restaurant
        cart.restaurant = restaurant
        cart.save()
        
        return Response({
            "message": f"Switched to {restaurant.name}. Previous cart items were cleared.",
            "cart": CartSerializer(cart).data
        })
    
    @extend_schema(
        summary="Checkout cart",
        description="Convert cart to order and process payment"
    )
    @action(detail=False, methods=['post'])
    def checkout(self, request):
        serializer = CheckoutSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        
        cart = self.get_object()
        
        if not cart.items.exists():
            return Response(
                {"error": "Cart is empty."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            with transaction.atomic():
                from orders.models import Order, OrderItem
                from geography.models import Address
                
                # Get validated data
                delivery_address = Address.objects.get(id=serializer.validated_data['delivery_address_id'])
                payment_method_id = serializer.validated_data['payment_method_id']
                delivery_instructions = serializer.validated_data.get('delivery_instructions', '')
                scheduled_for = serializer.validated_data.get('scheduled_for')
                tip_amount = serializer.validated_data.get('tip_amount', 0)
                
                # Create order
                order = Order.objects.create(
                    customer=request.user,
                    restaurant=cart.restaurant,
                    delivery_address=delivery_address.get_full_address(),
                    delivery_lat=delivery_address.latitude,
                    delivery_lng=delivery_address.longitude,
                    total_price=cart.total + tip_amount,
                    delivery_fee=cart.delivery_fee,
                    notes=delivery_instructions,
                    estimated_delivery_time=scheduled_for
                )
                
                # Create order items from cart items
                for cart_item in cart.items.all():
                    OrderItem.objects.create(
                        order=order,
                        menu_item=cart_item.menu_item,
                        quantity=cart_item.quantity,
                        unit_price=cart_item.unit_price,
                        subtotal=cart_item.total_price,
                        notes=cart_item.special_instructions
                    )
                
                # Process coupon usage if applied
                if cart.applied_coupon:
                    from promotions.models import CouponUsage
                    CouponUsage.objects.create(
                        coupon=cart.applied_coupon,
                        user=request.user,
                        order=order,
                        discount_amount=cart.discount_amount
                    )
                    
                    # Update coupon usage count
                    cart.applied_coupon.current_uses += 1
                    cart.applied_coupon.save()
                
                # Process loyalty points if used
                if cart.loyalty_points_used > 0:
                    from promotions.models import LoyaltyAccount, LoyaltyTransaction
                    try:
                        loyalty_account = request.user.loyalty_account
                        old_balance = loyalty_account.points_balance
                        loyalty_account.points_balance -= cart.loyalty_points_used
                        loyalty_account.total_points_redeemed += cart.loyalty_points_used
                        loyalty_account.save()
                        
                        LoyaltyTransaction.objects.create(
                            account=loyalty_account,
                            type='REDEEMED',
                            points=-cart.loyalty_points_used,
                            description=f"Points used for order #{order.id}",
                            reference_order=order,
                            balance_before=old_balance,
                            balance_after=loyalty_account.points_balance
                        )
                    except:
                        pass  # Ignore loyalty errors for now
                
                # Clear cart after successful order creation
                cart.clear()
                
                # Create payment (simplified)
                from payments.models import Payment, PaymentMethod
                payment_method = PaymentMethod.objects.get(id=payment_method_id)
                
                payment = Payment.objects.create(
                    order=order,
                    payment_method=payment_method,
                    amount=order.total_price,
                    status='PENDING'
                )
                
                return Response({
                    "message": "Order placed successfully.",
                    "order_id": order.id,
                    "payment_id": payment.id,
                    "total_amount": order.total_price
                }, status=status.HTTP_201_CREATED)
                
        except Exception as e:
            return Response(
                {"error": f"Checkout failed: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )


@extend_schema_view(
    list=extend_schema(summary="List favorites", description="Get user's favorite restaurants and menu items"),
    retrieve=extend_schema(summary="Get favorite details", description="Get specific favorite details"),
    create=extend_schema(summary="Add favorite", description="Add restaurant or menu item to favorites"),
    destroy=extend_schema(summary="Remove favorite", description="Remove from favorites"),
)
class CustomerFavoriteViewSet(viewsets.ModelViewSet):
    """ViewSet for managing customer favorites"""
    serializer_class = CustomerFavoriteSerializer
    permission_classes = [permissions.IsAuthenticated, IsCustomer]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['type']
    http_method_names = ['get', 'post', 'delete', 'head', 'options']
    
    def get_queryset(self):
        return CustomerFavorite.objects.filter(user=self.request.user)


@extend_schema_view(
    list=extend_schema(summary="List saved carts", description="Get user's saved carts"),
    retrieve=extend_schema(summary="Get saved cart details", description="Get specific saved cart details"),
    create=extend_schema(summary="Save current cart", description="Save current cart for later"),
    destroy=extend_schema(summary="Delete saved cart", description="Delete a saved cart"),
)
class SavedCartViewSet(viewsets.ModelViewSet):
    """ViewSet for managing saved carts"""
    serializer_class = SavedCartSerializer
    permission_classes = [permissions.IsAuthenticated, IsCustomer]
    http_method_names = ['get', 'post', 'delete', 'head', 'options']
    
    def get_queryset(self):
        return SavedCart.objects.filter(user=self.request.user)
    
    @extend_schema(
        summary="Load saved cart",
        description="Load a saved cart into current cart"
    )
    @action(detail=True, methods=['post'])
    def load_to_cart(self, request, pk=None):
        saved_cart = self.get_object()
        cart = Cart.objects.get_or_create(user=request.user)[0]
        
        # Clear current cart
        cart.clear()
        
        # Load saved cart data
        cart.restaurant = saved_cart.restaurant
        cart_data = saved_cart.cart_data
        
        # Recreate cart items
        for item_data in cart_data.get('items', []):
            try:
                menu_item = MenuItem.objects.get(id=item_data['menu_item_id'])
                CartItem.objects.create(
                    cart=cart,
                    menu_item=menu_item,
                    quantity=item_data['quantity'],
                    special_instructions=item_data.get('special_instructions', '')
                )
            except MenuItem.DoesNotExist:
                continue  # Skip items that no longer exist
        
        cart.calculate_totals()
        
        return Response({
            "message": "Saved cart loaded successfully.",
            "cart": CartSerializer(cart).data
        })


@extend_schema_view(
    list=extend_schema(summary="List quick reorders", description="Get user's quick reorder templates"),
    retrieve=extend_schema(summary="Get quick reorder details", description="Get specific quick reorder details"),
    create=extend_schema(summary="Create quick reorder", description="Create a quick reorder template"),
    destroy=extend_schema(summary="Delete quick reorder", description="Delete a quick reorder template"),
)
class QuickReorderViewSet(viewsets.ModelViewSet):
    """ViewSet for managing quick reorder templates"""
    serializer_class = QuickReorderSerializer
    permission_classes = [permissions.IsAuthenticated, IsCustomer]
    http_method_names = ['get', 'post', 'delete', 'head', 'options']
    
    def get_queryset(self):
        return QuickReorder.objects.filter(user=self.request.user).order_by('-use_count', '-last_used')
    
    @extend_schema(
        summary="Use quick reorder",
        description="Add quick reorder items to current cart"
    )
    @action(detail=True, methods=['post'])
    def use(self, request, pk=None):
        quick_reorder = self.get_object()
        cart = Cart.objects.get_or_create(user=request.user)[0]
        
        # Check if cart is empty or from same restaurant
        if cart.restaurant and cart.restaurant != quick_reorder.restaurant:
            return Response(
                {
                    "error": "Cannot add items from different restaurants. Clear cart first.",
                    "current_restaurant": cart.restaurant.name,
                    "quick_reorder_restaurant": quick_reorder.restaurant.name
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Set restaurant if cart is empty
        if not cart.restaurant:
            cart.restaurant = quick_reorder.restaurant
            cart.save()
        
        # Add items from quick reorder
        items_data = quick_reorder.items_data
        added_items = 0
        
        for item_data in items_data.get('items', []):
            try:
                menu_item = MenuItem.objects.get(id=item_data['menu_item_id'], is_available=True)
                cart_item, created = CartItem.objects.get_or_create(
                    cart=cart,
                    menu_item=menu_item,
                    defaults={
                        'quantity': item_data['quantity'],
                        'special_instructions': item_data.get('special_instructions', '')
                    }
                )
                
                if not created:
                    cart_item.quantity += item_data['quantity']
                    cart_item.save()
                
                added_items += 1
                
            except MenuItem.DoesNotExist:
                continue  # Skip unavailable items
        
        # Update quick reorder usage
        quick_reorder.last_used = timezone.now()
        quick_reorder.use_count += 1
        quick_reorder.save()
        
        cart.calculate_totals()
        
        return Response({
            "message": f"Added {added_items} items from quick reorder to cart.",
            "cart": CartSerializer(cart).data
        })


@extend_schema_view(
    list=extend_schema(summary="List recent orders", description="Get user's recent orders for reordering"),
    retrieve=extend_schema(summary="Get recent order details", description="Get specific recent order details"),
)
class RecentOrderViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing recent orders"""
    serializer_class = RecentOrderSerializer
    permission_classes = [permissions.IsAuthenticated, IsCustomer]
    
    def get_queryset(self):
        return RecentOrder.objects.filter(user=self.request.user)[:10]  # Last 10 orders
    
    @extend_schema(
        summary="Reorder",
        description="Add items from a recent order to current cart"
    )
    @action(detail=True, methods=['post'])
    def reorder(self, request, pk=None):
        recent_order = self.get_object()
        cart = Cart.objects.get_or_create(user=request.user)[0]
        
        # Check if cart is empty or from same restaurant
        if cart.restaurant and cart.restaurant != recent_order.restaurant:
            return Response(
                {
                    "error": "Cannot add items from different restaurants. Clear cart first.",
                    "current_restaurant": cart.restaurant.name,
                    "reorder_restaurant": recent_order.restaurant.name
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Set restaurant if cart is empty
        if not cart.restaurant:
            cart.restaurant = recent_order.restaurant
            cart.save()
        
        # Add items from recent order
        order_summary = recent_order.order_summary
        added_items = 0
        
        for item_data in order_summary.get('items', []):
            try:
                menu_item = MenuItem.objects.get(id=item_data['menu_item_id'], is_available=True)
                cart_item, created = CartItem.objects.get_or_create(
                    cart=cart,
                    menu_item=menu_item,
                    defaults={
                        'quantity': item_data['quantity'],
                        'special_instructions': item_data.get('special_instructions', '')
                    }
                )
                
                if not created:
                    cart_item.quantity += item_data['quantity']
                    cart_item.save()
                
                added_items += 1
                
            except MenuItem.DoesNotExist:
                continue  # Skip unavailable items
        
        cart.calculate_totals()
        
        return Response({
            "message": f"Added {added_items} items from recent order to cart.",
            "cart": CartSerializer(cart).data
        })


@extend_schema_view(
    list=extend_schema(summary="List menu customizations", description="Get customization options for menu items"),
    retrieve=extend_schema(summary="Get customization details", description="Get specific customization details"),
)
class MenuItemCustomizationViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing menu item customizations"""
    serializer_class = MenuItemCustomizationSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['menu_item']
    
    def get_queryset(self):
        return MenuItemCustomization.objects.filter(menu_item__is_available=True).order_by('order')
