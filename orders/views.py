from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count # Import Count
from .models import Order, OrderItem, OrderStatusUpdate
from .serializers import (
    OrderSerializer,
    OrderListSerializer,
    OrderItemSerializer,
    OrderStatusUpdateSerializer,
    OrderUpdateSerializer,
    OrderDetailSerializer # Added
)
from .filters import OrderFilter
from users.permissions import IsCustomer, IsRestaurantOwner, IsDriver, IsAdminUser
from drf_spectacular.utils import extend_schema, extend_schema_view


class OrderPagination(PageNumberPagination):
    """Custom pagination for orders with 20 items per page"""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


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
        
        # any authenticated user can view their own orders
        return request.user.is_authenticated


@extend_schema_view(
    list=extend_schema(summary="List orders", description="Get a list of orders based on user role", tags=['Core Business Operations']),
    retrieve=extend_schema(summary="Get order details", description="Retrieve detailed information about a specific order", tags=['Core Business Operations']),
    create=extend_schema(summary="Create order", description="Create a new order (Customer only)", tags=['Core Business Operations']),
    update=extend_schema(summary="Update order", description="Update order details", tags=['Core Business Operations']),
    partial_update=extend_schema(summary="Partial update order", description="Partially update order details", tags=['Core Business Operations']),
)
class OrderViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Order model that adapts to user role.
    - Customers see their own orders
    - Restaurant owners see orders for their restaurant
    - Drivers see orders assigned to them
    - Admins see all orders
    """
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter]
    filterset_class = OrderFilter
    ordering_fields = ['created_at', 'updated_at', 'total_price']
    ordering = ['-created_at']
    search_fields = ['customer__first_name', 'customer__last_name', 'id']
    permission_classes = [OrderPermission]
    pagination_class = OrderPagination
    tags = ['Core Business Operations']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return OrderListSerializer
        elif self.action == 'retrieve': # Added this condition
            return OrderDetailSerializer
        elif self.action == 'update' or self.action == 'partial_update':
            return OrderUpdateSerializer
        return OrderSerializer # Default for create and other actions
    
    def get_queryset(self):
        user = self.request.user
        qs = Order.objects.none() # Default to no results

        if user.is_staff:
            qs = Order.objects.all().select_related('customer', 'restaurant')
        elif user.is_customer() and not (user.is_restaurant_owner() or user.is_driver()):
            qs = Order.objects.filter(customer=user).select_related('customer', 'restaurant')
        elif user.is_restaurant_owner():
            restaurants = user.restaurants.all()
            qs = Order.objects.filter(restaurant__in=restaurants).select_related('customer', 'restaurant')
        elif user.is_driver() and hasattr(user, 'driver_profile'):
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
        restaurants = request.user.restaurants
        if not hasattr(request.user, 'restaurants') or order.restaurant not in restaurants:
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
        if not hasattr(request.user, 'restaurants') or order.restaurant != user.restaurants.first():
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

        # Auto-assign driver when order is ready for pickup
        from .driver_assignment import assign_driver_to_order
        assign_driver_to_order(order)

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
        if not hasattr(request.user, 'restaurants') or order.restaurant != user.restaurants.first():
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
        
        # Auto-assign driver when order is ready for pickup
        from .driver_assignment import assign_driver_to_order
        if order.status == 'READY_FOR_PICKUP':
            assign_driver_to_order(order)
        
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
    
    @extend_schema(
        summary="Update order status",
        description="Update order status (Restaurant owner or Admin only)"
    )
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def update_status(self, request, pk=None):
        order = self.get_object()
        new_status = request.data.get('status')
        note = request.data.get('note', '')
        
        if not new_status:
            return Response(
                {"error": "Status is required."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if the new status is valid
        valid_statuses = [choice[0] for choice in Order.ORDER_STATUS_CHOICES]
        if new_status not in valid_statuses:
            return Response(
                {"error": f"Invalid status. Valid options are: {', '.join(valid_statuses)}"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Permission check: only restaurant owners (for their orders) or admins can update status
        user = request.user
        if not user.is_staff:
            if user.is_restaurant_owner():
                # Check if the order belongs to one of the user's restaurants
                user_restaurants = user.restaurants.all()
                if order.restaurant not in user_restaurants:
                    return Response(
                        {"error": "You can only update status for orders from your restaurants."},
                        status=status.HTTP_403_FORBIDDEN
                    )
            else:
                return Response(
                    {"error": "You don't have permission to update order status."},
                    status=status.HTTP_403_FORBIDDEN
                )
        
        # Update the status
        try:
            order.update_status(new_status, user, notes=note)
            serializer = self.get_serializer(order)
            return Response({
                "message": f"Order status updated to {new_status}",
                "order": serializer.data
            })
        except Exception as e:
            return Response(
                {"error": f"Failed to update status: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )