from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
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
        
        # Admin can see all orders
        if user.is_staff:
            return Order.objects.all().select_related('customer', 'restaurant')
        
        # Customer can only see their own orders
        if user.role == 'CUSTOMER':
            return Order.objects.filter(customer=user).select_related('customer', 'restaurant')
        
        # Restaurant owner can see orders for their restaurant
        if user.role == 'RESTAURANT' and hasattr(user, 'restaurant'):
            return Order.objects.filter(restaurant=user.restaurant).select_related('customer', 'restaurant')
        
        # Driver can see orders assigned to them
        if user.role == 'DRIVER' and hasattr(user, 'driver_profile'):
            # Return orders where the driver is assigned
            return Order.objects.filter(
                driver_task__driver__user=user
            ).select_related('customer', 'restaurant')
        
        return Order.objects.none()
    
    def get_permissions(self):
        if self.action == 'create':
            permission_classes = [permissions.IsAuthenticated, IsCustomer]
        else:
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
            order.status = 'CONFIRMED'
            status_note = note or "Order confirmed by restaurant."
        else:  # reject
            order.status = 'CANCELLED'
            status_note = note or "Order rejected by restaurant."
        
        order.save()
        
        # Create status update
        OrderStatusUpdate.objects.create(
            order=order,
            status=order.status,
            updated_by=request.user,
            notes=status_note
        )
        
        serializer = OrderSerializer(order, context={'request': request})
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
        
        order.status = 'PREPARING'
        order.save()
        
        # Create status update
        OrderStatusUpdate.objects.create(
            order=order,
            status='PREPARING',
            updated_by=request.user,
            notes=note
        )
        
        serializer = OrderSerializer(order, context={'request': request})
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
        
        order.status = 'CANCELLED'
        order.save()
        
        # Create status update
        OrderStatusUpdate.objects.create(
            order=order,
            status='CANCELLED',
            updated_by=request.user,
            notes=reason
        )
        
        serializer = OrderSerializer(order, context={'request': request})
        return Response(serializer.data)