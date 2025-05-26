from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count # Import Count
from .models import Order, OrderItem, OrderStatusUpdate
from .serializers import (
    OrderSerializer,
    OrderListSerializer,
    OrderItemSerializer,
    OrderStatusUpdateSerializer,
    OrderUpdateSerializer
)
from users.permissions import IsCustomer, IsRestaurantOwner, IsDriver, IsAdminUser
from drf_spectacular.utils import extend_schema, extend_schema_view


class OrderPermission(permissions.BasePermission):
    """
    Custom permission for orders:
    - Customers can view their own orders
    - Restaurant owners can view orders for their restaurant
    - Drivers can view orders assigned to them
    - Admins can view all orders
    """
    def has_permission(self, request, view):
        # Allow authenticated users
        return request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        # Admin can do anything
        if request.user.is_staff:
            return True
        
        # Customer can only view their own orders
        if request.user.role == 'CUSTOMER':
            return obj.customer == request.user
        
        # Restaurant owner can view orders for their restaurant
        if request.user.role == 'RESTAURANT':
            if hasattr(request.user, 'restaurant'):
                return obj.restaurant == request.user.restaurant
            return False
        
        # Driver can view orders assigned to them
        if request.user.role == 'DRIVER':
            if hasattr(request.user, 'driver_profile'):
                # Check if driver is assigned to this order
                try:
                    return obj.driver_task.driver.user == request.user
                except AttributeError:
                    return False
            return False
        
        return False


@extend_schema_view(
    list=extend_schema(summary="List orders", description="Get a list of orders based on user role"),
    retrieve=extend_schema(summary="Get order details", description="Retrieve detailed information about a specific order"),
    create=extend_schema(summary="Create order", description="Create a new order (Customer only)"),
    update=extend_schema(summary="Update order", description="Update order details"),
    partial_update=extend_schema(summary="Partial update order", description="Partially update order details"),
)
class OrderViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Order model that adapts to user role.
    - Customers see their own orders
    - Restaurant owners see orders for their restaurant
    - Drivers see orders assigned to them
    - Admins see all orders
    """
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status', 'restaurant']
    ordering_fields = ['created_at', 'updated_at', 'total_price']
    ordering = ['-created_at']
    permission_classes = [OrderPermission]
    
    def get_serializer_class(self):
        if self.action == 'list':
            return OrderListSerializer
        elif self.action == 'update' or self.action == 'partial_update':
            return OrderUpdateSerializer
        return OrderSerializer
    
    def get_queryset(self):
        user = self.request.user
        qs = Order.objects.none() # Default to no results

        if user.is_staff:
            qs = Order.objects.all().select_related('customer', 'restaurant')
        elif user.role == 'CUSTOMER':
            qs = Order.objects.filter(customer=user).select_related('customer', 'restaurant')
        elif user.role == 'RESTAURANT' and hasattr(user, 'restaurant'):
            qs = Order.objects.filter(restaurant=user.restaurant).select_related('customer', 'restaurant')
        elif user.role == 'DRIVER' and hasattr(user, 'driver_profile'):
            qs = Order.objects.filter(driver_task__driver__user=user).select_related('customer', 'restaurant')
        
        # If qs is still Order.objects.none(), no need to apply further optimizations
        if qs.model == Order.objects.none().model and not qs.exists(): # Check if it's still the empty queryset
             return qs

        if self.action == 'list':
            qs = qs.annotate(item_count=Count('items')).prefetch_related('items')
        elif self.action == 'retrieve': # This also applies to other detail-view actions like 'history', 'update', etc.
            qs = qs.prefetch_related('items', 'status_updates')
        # For other actions like 'create', 'update', 'partial_update', the base qs is fine as they typically operate on a single instance
        # or don't require these specific prefetches for their primary operation.
        # Custom actions like 'history' will benefit from 'retrieve's prefetching if they call get_object().
        
        return qs
    
    def get_permissions(self):
        if self.action == 'create':
            permission_classes = [permissions.IsAuthenticated, IsCustomer]
        elif self.action in ['update', 'partial_update']:
            permission_classes = [permissions.IsAuthenticated, IsAdminUser]
        else:
            # For list, retrieve, and custom actions, use the existing OrderPermission
            # OrderPermission itself will handle role-specific access (e.g., customer sees own orders)
            permission_classes = [OrderPermission]
        return [permission() for permission in permission_classes]
    
    @extend_schema(
        summary="Get order history",
        description="Get status history for a specific order"
    )
    @action(detail=True, methods=['get'])
    def history(self, request, pk=None):
        order = self.get_object()
        status_updates = order.status_updates.all()
        serializer = OrderStatusUpdateSerializer(status_updates, many=True)
        return Response(serializer.data)
    
    @extend_schema(
        summary="Restaurant accept/reject order",
        description="Restaurant owner can accept or reject an order"
    )
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated, IsRestaurantOwner])
    def restaurant_action(self, request, pk=None):
        order = self.get_object()
        action = request.data.get('action')
        note = request.data.get('note', '')
        
        if action not in ['accept', 'reject']:
            return Response(
                {"error": "Invalid action. Expected 'accept' or 'reject'."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Ensure the restaurant owns this order
        if not hasattr(request.user, 'restaurant') or order.restaurant != request.user.restaurant:
            return Response(
                {"error": "You can only perform actions on orders for your restaurant."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Ensure the order is in the correct state to be accepted/rejected
        if order.status != 'PLACED':
            return Response(
                {"error": f"Cannot {action} order. Current status is {order.status}."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if action == 'accept':
            status_note = note or "Order confirmed by restaurant."
            order.update_status('CONFIRMED', request.user, notes=status_note)
        else:  # reject
            status_note = note or "Order rejected by restaurant."
            order.update_status('CANCELLED', request.user, notes=status_note)
        
        serializer = self.get_serializer(order)
        return Response(serializer.data)

    @extend_schema(
        summary="Mark order ready for pickup",
        description="Restaurant owner can mark an order as ready for pickup"
    )
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated, IsRestaurantOwner])
    def mark_ready_for_pickup(self, request, pk=None):
        order = self.get_object()
        note = request.data.get('note', 'Order is ready for pickup.')

        # Ensure the restaurant owns this order
        if not hasattr(request.user, 'restaurant') or order.restaurant != request.user.restaurant:
            return Response(
                {"error": "You can only perform actions on orders for your restaurant."},
                status=status.HTTP_403_FORBIDDEN
            )

        # Ensure the order is in the correct state
        if order.status != 'PREPARING':
            return Response(
                {"error": f"Cannot mark order as ready for pickup. Current status is {order.status}."},
                status=status.HTTP_400_BAD_REQUEST
            )

        order.update_status('READY_FOR_PICKUP', request.user, notes=note)

        serializer = self.get_serializer(order)
        return Response(serializer.data)
    
    @extend_schema(
        summary="Mark order as preparing",
        description="Restaurant owner can mark an order as being prepared"
    )
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated, IsRestaurantOwner])
    def preparing(self, request, pk=None):
        order = self.get_object()
        note = request.data.get('note', 'Order is being prepared.')
        
        # Ensure the restaurant owns this order
        if not hasattr(request.user, 'restaurant') or order.restaurant != request.user.restaurant:
            return Response(
                {"error": "You can only perform actions on orders for your restaurant."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Ensure the order is in the correct state
        if order.status != 'CONFIRMED':
            return Response(
                {"error": f"Cannot mark order as preparing. Current status is {order.status}."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        order.update_status('PREPARING', request.user, notes=note)
        
        serializer = self.get_serializer(order)
        return Response(serializer.data)
    
    @extend_schema(
        summary="Cancel order",
        description="Customer can cancel an order if it's still in PLACED or CONFIRMED status"
    )
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated, IsCustomer])
    def cancel(self, request, pk=None):
        order = self.get_object()
        
        # Ensure the customer owns this order
        if order.customer != request.user:
            return Response(
                {"error": "You can only cancel your own orders."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Ensure the order is in a cancellable state
        if order.status not in ['PLACED', 'CONFIRMED']:
            return Response(
                {"error": f"Cannot cancel order. Current status is {order.status}. Orders can only be cancelled before preparation begins."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        reason = request.data.get('reason', 'Cancelled by customer.')
        
        order.update_status('CANCELLED', request.user, notes=reason)
        
        serializer = self.get_serializer(order)
        return Response(serializer.data)