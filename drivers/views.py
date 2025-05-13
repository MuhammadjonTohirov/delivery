from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Sum, Count
from django.utils import timezone
from datetime import timedelta
from django_filters.rest_framework import DjangoFilterBackend

from users.models import DriverProfile
from .models import DriverLocation, DriverAvailability, DriverTask, DriverEarning
from .serializers import (
    DriverLocationSerializer,
    DriverAvailabilitySerializer,
    DriverTaskSerializer,
    DriverEarningSerializer,
    DriverEarningSummarySerializer
)
from users.permissions import IsDriver, IsAdminUser
from drf_spectacular.utils import extend_schema, extend_schema_view


class DriverPermission(permissions.BasePermission):
    """
    Custom permission for driver actions:
    - Drivers can only access their own data
    - Admins can access all data
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and (request.user.role == 'DRIVER' or request.user.is_staff)
    
    def has_object_permission(self, request, view, obj):
        if request.user.is_staff:
            return True
        
        # Check if the object belongs to the driver
        if hasattr(obj, 'driver'):
            return obj.driver.user == request.user
        return False


@extend_schema_view(
    list=extend_schema(summary="List driver locations", description="List of driver location updates"),
    retrieve=extend_schema(summary="Get location details", description="Get details of a specific location update"),
    create=extend_schema(summary="Create location update", description="Create a new location update (Driver only)"),
)
class DriverLocationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for reporting and retrieving driver locations.
    """
    serializer_class = DriverLocationSerializer
    permission_classes = [DriverPermission]
    http_method_names = ['get', 'post', 'head', 'options']  # Only allow GET and POST
    
    def get_queryset(self):
        user = self.request.user
        
        # Admin can see all locations
        if user.is_staff:
            return DriverLocation.objects.all()
        
        # Driver can only see their own locations
        if user.role == 'DRIVER' and hasattr(user, 'driver_profile'):
            return DriverLocation.objects.filter(driver=user.driver_profile)
        
        return DriverLocation.objects.none()
    
    @extend_schema(
        summary="Get latest location",
        description="Get the latest location for the current driver or a specific driver"
    )
    @action(detail=False, methods=['get'])
    def latest(self, request):
        user = request.user
        driver_id = request.query_params.get('driver_id')
        
        if driver_id and user.is_staff:
            # Admin can get latest location for any driver
            try:
                latest_location = DriverLocation.objects.filter(
                    driver_id=driver_id
                ).latest('timestamp')
                serializer = self.get_serializer(latest_location)
                return Response(serializer.data)
            except DriverLocation.DoesNotExist:
                return Response(
                    {"error": "No location found for this driver."},
                    status=status.HTTP_404_NOT_FOUND
                )
        
        # Driver can get their own latest location
        if user.role == 'DRIVER' and hasattr(user, 'driver_profile'):
            try:
                latest_location = DriverLocation.objects.filter(
                    driver=user.driver_profile
                ).latest('timestamp')
                serializer = self.get_serializer(latest_location)
                return Response(serializer.data)
            except DriverLocation.DoesNotExist:
                return Response(
                    {"error": "No location found."},
                    status=status.HTTP_404_NOT_FOUND
                )
        
        return Response(
            {"error": "You do not have permission to view this data."},
            status=status.HTTP_403_FORBIDDEN
        )


@extend_schema_view(
    retrieve=extend_schema(summary="Get driver availability", description="Get availability status of a driver"),
    update=extend_schema(summary="Update availability", description="Update driver availability status"),
    partial_update=extend_schema(summary="Partial update availability", description="Partially update driver availability"),
)
class DriverAvailabilityViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing driver availability.
    """
    serializer_class = DriverAvailabilitySerializer
    permission_classes = [DriverPermission]
    http_method_names = ['get', 'put', 'patch', 'head', 'options']  # No POST or DELETE
    
    def get_queryset(self):
        user = self.request.user
        
        # Admin can see all availabilities
        if user.is_staff:
            return DriverAvailability.objects.all()
        
        # Driver can only see their own availability
        if user.role == 'DRIVER' and hasattr(user, 'driver_profile'):
            return DriverAvailability.objects.filter(driver=user.driver_profile)
        
        return DriverAvailability.objects.none()
    
    @extend_schema(
        summary="Get my availability",
        description="Get current driver's availability status"
    )
    @action(detail=False, methods=['get'])
    def me(self, request):
        user = request.user
        
        if user.role == 'DRIVER' and hasattr(user, 'driver_profile'):
            try:
                availability = DriverAvailability.objects.get(driver=user.driver_profile)
                serializer = self.get_serializer(availability)
                return Response(serializer.data)
            except DriverAvailability.DoesNotExist:
                # Create default availability record
                availability = DriverAvailability.objects.create(
                    driver=user.driver_profile,
                    status='OFFLINE'
                )
                serializer = self.get_serializer(availability)
                return Response(serializer.data)
        
        return Response(
            {"error": "You do not have permission to view this data."},
            status=status.HTTP_403_FORBIDDEN
        )
    
    @extend_schema(
        summary="Go online",
        description="Set driver status to AVAILABLE"
    )
    @action(detail=False, methods=['post'])
    def go_online(self, request):
        user = request.user
        
        if user.role == 'DRIVER' and hasattr(user, 'driver_profile'):
            availability, created = DriverAvailability.objects.get_or_create(
                driver=user.driver_profile,
                defaults={'status': 'AVAILABLE'}
            )
            
            if not created:
                availability.status = 'AVAILABLE'
                availability.save()
            
            serializer = self.get_serializer(availability)
            return Response(serializer.data)
        
        return Response(
            {"error": "You do not have permission to perform this action."},
            status=status.HTTP_403_FORBIDDEN
        )
    
    @extend_schema(
        summary="Go offline",
        description="Set driver status to OFFLINE"
    )
    @action(detail=False, methods=['post'])
    def go_offline(self, request):
        user = request.user
        
        if user.role == 'DRIVER' and hasattr(user, 'driver_profile'):
            availability, created = DriverAvailability.objects.get_or_create(
                driver=user.driver_profile,
                defaults={'status': 'OFFLINE'}
            )
            
            if not created:
                availability.status = 'OFFLINE'
                availability.save()
            
            serializer = self.get_serializer(availability)
            return Response(serializer.data)
        
        return Response(
            {"error": "You do not have permission to perform this action."},
            status=status.HTTP_403_FORBIDDEN
        )


@extend_schema_view(
    list=extend_schema(summary="List driver tasks", description="List all tasks for a driver"),
    retrieve=extend_schema(summary="Get task details", description="Get details of a specific task"),
    update=extend_schema(summary="Update task", description="Update task status (Driver only)"),
    partial_update=extend_schema(summary="Partial update task", description="Partially update task status (Driver only)"),
)
class DriverTaskViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing driver tasks.
    """
    serializer_class = DriverTaskSerializer
    permission_classes = [DriverPermission]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status']
    ordering_fields = ['assigned_at', 'accepted_at', 'completed_at']
    ordering = ['-assigned_at']
    http_method_names = ['get', 'put', 'patch', 'head', 'options']  # No POST or DELETE
    
    def get_queryset(self):
        user = self.request.user
        
        # Admin can see all tasks
        if user.is_staff:
            return DriverTask.objects.all()
        
        # Driver can only see their own tasks
        if user.role == 'DRIVER' and hasattr(user, 'driver_profile'):
            return DriverTask.objects.filter(driver=user.driver_profile)
        
        return DriverTask.objects.none()
    
    @extend_schema(
        summary="Accept task",
        description="Driver accepts a task assignment"
    )
    @action(detail=True, methods=['post'])
    def accept(self, request, pk=None):
        task = self.get_object()
        
        if task.status != 'PENDING':
            return Response(
                {"error": f"Cannot accept task. Current status is {task.status}."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = self.get_serializer(task, data={'status': 'ACCEPTED'}, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response(serializer.data)
    
    @extend_schema(
        summary="Reject task",
        description="Driver rejects a task assignment"
    )
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        task = self.get_object()
        
        if task.status != 'PENDING':
            return Response(
                {"error": f"Cannot reject task. Current status is {task.status}."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = self.get_serializer(task, data={'status': 'REJECTED'}, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response(serializer.data)
    
    @extend_schema(
        summary="Mark as picked up",
        description="Driver marks a task as picked up"
    )
    @action(detail=True, methods=['post'])
    def picked_up(self, request, pk=None):
        task = self.get_object()
        
        if task.status != 'ACCEPTED':
            return Response(
                {"error": f"Cannot mark as picked up. Current status is {task.status}."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = self.get_serializer(task, data={'status': 'PICKED_UP'}, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response(serializer.data)
    
    @extend_schema(
        summary="Mark as delivered",
        description="Driver marks a task as delivered"
    )
    @action(detail=True, methods=['post'])
    def delivered(self, request, pk=None):
        task = self.get_object()
        
        if task.status != 'PICKED_UP':
            return Response(
                {"error": f"Cannot mark as delivered. Current status is {task.status}."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = self.get_serializer(task, data={'status': 'DELIVERED'}, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response(serializer.data)
    
    @extend_schema(
        summary="Get active task",
        description="Get the driver's current active task"
    )
    @action(detail=False, methods=['get'])
    def active(self, request):
        user = request.user
        
        if user.role == 'DRIVER' and hasattr(user, 'driver_profile'):
            # Get the most recent non-completed task
            active_task = DriverTask.objects.filter(
                driver=user.driver_profile,
                status__in=['PENDING', 'ACCEPTED', 'PICKED_UP']
            ).order_by('-assigned_at').first()
            
            if active_task:
                serializer = self.get_serializer(active_task)
                return Response(serializer.data)
            else:
                return Response(
                    {"message": "No active tasks found."},
                    status=status.HTTP_404_NOT_FOUND
                )
        
        return Response(
            {"error": "You do not have permission to view this data."},
            status=status.HTTP_403_FORBIDDEN
        )


@extend_schema_view(
    list=extend_schema(summary="List earnings", description="List all earnings for a driver"),
    retrieve=extend_schema(summary="Get earning details", description="Get details of a specific earning"),
)
class DriverEarningViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for retrieving driver earnings.
    """
    serializer_class = DriverEarningSerializer
    permission_classes = [DriverPermission]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['is_bonus']
    ordering_fields = ['timestamp', 'amount']
    ordering = ['-timestamp']
    
    def get_queryset(self):
        user = self.request.user
        
        # Admin can see all earnings
        if user.is_staff:
            return DriverEarning.objects.all()
        
        # Driver can only see their own earnings
        if user.role == 'DRIVER' and hasattr(user, 'driver_profile'):
            return DriverEarning.objects.filter(driver=user.driver_profile)
        
        return DriverEarning.objects.none()
    
    @extend_schema(
        summary="Get earnings summary",
        description="Get a summary of driver earnings for a specified period"
    )
    @action(detail=False, methods=['get'])
    def summary(self, request):
        user = request.user
        
        # Get date range from parameters (default: last 7 days)
        days = int(request.query_params.get('days', 7))
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        
        if user.role == 'DRIVER' and hasattr(user, 'driver_profile'):
            driver = user.driver_profile
            
            # Query earnings within the date range
            earnings_query = DriverEarning.objects.filter(
                driver=driver,
                timestamp__gte=start_date,
                timestamp__lte=end_date
            )
            
            # Calculate summary data
            total_earnings = earnings_query.aggregate(Sum('amount'))['amount__sum'] or 0
            total_deliveries = earnings_query.filter(is_bonus=False).count()
            
            summary_data = {
                'driver': driver.id,
                'driver_name': driver.user.full_name,
                'total_earnings': total_earnings,
                'total_deliveries': total_deliveries,
                'start_date': start_date,
                'end_date': end_date
            }
            
            serializer = DriverEarningSummarySerializer(summary_data)
            return Response(serializer.data)
        
        # Admin can get summary for any driver
        if user.is_staff:
            driver_id = request.query_params.get('driver_id')
            
            if not driver_id:
                return Response(
                    {"error": "Driver ID is required."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            try:
                driver = DriverProfile.objects.get(id=driver_id)
                
                # Query earnings within the date range
                earnings_query = DriverEarning.objects.filter(
                    driver=driver,
                    timestamp__gte=start_date,
                    timestamp__lte=end_date
                )
                
                # Calculate summary data
                total_earnings = earnings_query.aggregate(Sum('amount'))['amount__sum'] or 0
                total_deliveries = earnings_query.filter(is_bonus=False).count()
                
                summary_data = {
                    'driver': driver.id,
                    'driver_name': driver.user.full_name,
                    'total_earnings': total_earnings,
                    'total_deliveries': total_deliveries,
                    'start_date': start_date,
                    'end_date': end_date
                }
                
                serializer = DriverEarningSummarySerializer(summary_data)
                return Response(serializer.data)
            except DriverProfile.DoesNotExist:
                return Response(
                    {"error": "Driver not found."},
                    status=status.HTTP_404_NOT_FOUND
                )
        
        return Response(
            {"error": "You do not have permission to view this data."},
            status=status.HTTP_403_FORBIDDEN
        )