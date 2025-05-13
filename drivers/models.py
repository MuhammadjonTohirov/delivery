from django.db import models
from django.conf import settings
from orders.models import Order
import uuid


class DriverLocation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    driver = models.ForeignKey('users.DriverProfile', on_delete=models.CASCADE, related_name='locations')
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    accuracy = models.FloatField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
        get_latest_by = 'timestamp'
    
    def __str__(self):
        return f"Driver {self.driver.user.full_name} at {self.timestamp}"


class DriverAvailability(models.Model):
    AVAILABILITY_CHOICES = (
        ('AVAILABLE', 'Available'),
        ('BUSY', 'Busy'),
        ('OFFLINE', 'Offline'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    driver = models.OneToOneField('users.DriverProfile', on_delete=models.CASCADE, related_name='availability')
    status = models.CharField(max_length=20, choices=AVAILABILITY_CHOICES, default='OFFLINE')
    last_update = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Driver {self.driver.user.full_name} is {self.status}"


class DriverTask(models.Model):
    TASK_STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('ACCEPTED', 'Accepted'),
        ('REJECTED', 'Rejected'),
        ('PICKED_UP', 'Picked Up'),
        ('DELIVERED', 'Delivered'),
        ('CANCELLED', 'Cancelled'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    driver = models.ForeignKey('users.DriverProfile', on_delete=models.CASCADE, related_name='tasks')
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='driver_task')
    status = models.CharField(max_length=20, choices=TASK_STATUS_CHOICES, default='PENDING')
    assigned_at = models.DateTimeField(auto_now_add=True)
    accepted_at = models.DateTimeField(null=True, blank=True)
    picked_up_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['-assigned_at']
    
    def __str__(self):
        return f"Task for {self.driver.user.full_name} - Order {self.order.id}"


class DriverEarning(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    driver = models.ForeignKey('users.DriverProfile', on_delete=models.CASCADE, related_name='earnings')
    order = models.OneToOneField(Order, on_delete=models.SET_NULL, null=True, blank=True, related_name='driver_earning')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.CharField(max_length=255)
    is_bonus = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Earning for {self.driver.user.full_name} - {self.amount}"