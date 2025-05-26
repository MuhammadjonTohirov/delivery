from rest_framework import serializers
from .models import DriverLocation, DriverAvailability, DriverTask, DriverEarning
from users.models import DriverProfile
from django.utils import timezone
from orders.serializers import OrderListSerializer


class DriverLocationSerializer(serializers.ModelSerializer):
    driver_name = serializers.CharField(source='driver.user.full_name', read_only=True)
    
    class Meta:
        model = DriverLocation
        fields = ['id', 'driver', 'driver_name', 'latitude', 'longitude', 'accuracy', 'timestamp']
        read_only_fields = ['id', 'driver_name', 'timestamp']
    
    def create(self, validated_data):
        # Set driver as the current user's driver profile
        request = self.context.get('request')
        if request and hasattr(request.user, 'driver_profile'):
            validated_data['driver'] = request.user.driver_profile
        return super().create(validated_data)


class DriverAvailabilitySerializer(serializers.ModelSerializer):
    driver_name = serializers.CharField(source='driver.user.full_name', read_only=True)
    
    class Meta:
        model = DriverAvailability
        fields = ['id', 'driver', 'driver_name', 'status', 'last_update']
        read_only_fields = ['id', 'driver', 'driver_name', 'last_update']
    
    def update(self, instance, validated_data):
        instance.status = validated_data.get('status', instance.status)
        instance.save()
        return instance


class DriverTaskSerializer(serializers.ModelSerializer):
    driver_name = serializers.CharField(source='driver.user.full_name', read_only=True)
    order_details = OrderListSerializer(source='order', read_only=True)
    
    class Meta:
        model = DriverTask
        fields = ['id', 'driver', 'driver_name', 'order', 'order_details', 'status', 
                 'assigned_at', 'accepted_at', 'picked_up_at', 'completed_at', 'notes']
        read_only_fields = ['id', 'driver', 'driver_name', 'order', 'order_details', 
                           'assigned_at', 'accepted_at', 'picked_up_at', 'completed_at']
    
    def update(self, instance, validated_data):
        new_status = validated_data.get('status')
        notes = validated_data.get('notes')
        
        if new_status and new_status != instance.status:
            # Handle status transitions
            if new_status == 'ACCEPTED' and instance.status == 'PENDING':
                instance.accepted_at = timezone.now()
                # Order status is NOT changed here. It changes when driver picks up.
            elif new_status == 'PICKED_UP' and instance.status == 'ACCEPTED':
                instance.picked_up_at = timezone.now()
                # Update order status
                order = instance.order
                order.status = 'ON_THE_WAY'
                order.save()
            elif new_status == 'DELIVERED' and instance.status == 'PICKED_UP':
                instance.completed_at = timezone.now()
                # Update order status
                order = instance.order
                order.status = 'DELIVERED'
                order.save()
                
                # Create driver earning record for the completed delivery
                # This is a simplified example - in a real app, you might have more complex logic
                base_fee = 5.00  # Base delivery fee
                delivery_distance = 0  # Calculate based on order delivery and pickup locations
                
                # Simple earning calculation
                earning_amount = base_fee  # In a real app, add distance-based fee
                
                DriverEarning.objects.create(
                    driver=instance.driver,
                    order=order,
                    amount=earning_amount,
                    description=f"Delivery fee for order #{order.id}"
                )
            
            instance.status = new_status
        
        if notes:
            instance.notes = notes
        
        instance.save()
        return instance


class DriverEarningSerializer(serializers.ModelSerializer):
    driver_name = serializers.CharField(source='driver.user.full_name', read_only=True)
    order_id = serializers.UUIDField(source='order.id', read_only=True)
    
    class Meta:
        model = DriverEarning
        fields = ['id', 'driver', 'driver_name', 'order', 'order_id', 'amount', 
                  'description', 'is_bonus', 'timestamp']
        read_only_fields = ['id', 'driver', 'driver_name', 'order', 'order_id', 'timestamp']


class DriverEarningSummarySerializer(serializers.Serializer):
    """
    Serializer for summarizing driver earnings over a period.
    """
    driver = serializers.UUIDField(read_only=True)
    driver_name = serializers.CharField(read_only=True)
    total_earnings = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    total_deliveries = serializers.IntegerField(read_only=True)
    start_date = serializers.DateTimeField(read_only=True)
    end_date = serializers.DateTimeField(read_only=True)