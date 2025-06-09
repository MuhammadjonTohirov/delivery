from django.db import models
from django.conf import settings
from restaurants.models import Restaurant, MenuItem
import uuid

# Import the utility function to facilitate testing
from .utils import cancel_timed_out_orders


class Order(models.Model):
    ORDER_STATUS_CHOICES = (
        ('PLACED', 'Order Placed'),
        ('CONFIRMED', 'Order Confirmed'),
        ('PREPARING', 'Preparing'),
        ('READY_FOR_PICKUP', 'Ready for Pickup'),
        ('PICKED_UP', 'Picked Up'),
        ('ON_THE_WAY', 'On the Way'),
        ('DELIVERED', 'Delivered'),
        ('CANCELLED', 'Cancelled'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='orders')
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='orders')
    status = models.CharField(max_length=20, choices=ORDER_STATUS_CHOICES, default='PLACED')
    delivery_address = models.TextField()
    delivery_lat = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    delivery_lng = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    delivery_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Discount amount applied by restaurant")
    estimated_delivery_time = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Order {self.id} by {self.customer.full_name} at {self.restaurant.name}"
    
    def calculate_total_price(self):
        """Calculate total price based on order items, delivery fee, and discount"""
        items_total = sum(item.subtotal for item in self.items.all())
        total_before_discount = items_total + self.delivery_fee
        return max(0, total_before_discount - self.discount)  # Ensure total doesn't go below 0
    
    def save(self, *args, **kwargs):
        # For new orders, save first to get the ID for related items
        if not self.pk:
            super().save(*args, **kwargs)
        
        # Always recalculate total_price to ensure it's up to date
        self.total_price = self.calculate_total_price()
        super().save(*args, **kwargs)

    def update_status(self, new_status, updated_by_user, notes=""):
        # Ensure new_status is a valid choice.
        if new_status not in [choice[0] for choice in self.ORDER_STATUS_CHOICES]:
            # Or raise a ValueError, depending on desired handling
            print(f"Warning: Invalid status '{new_status}' attempted for order {self.id}") 
            return 

        self.status = new_status
        self.save()  # Save the Order instance first

        # Create the OrderStatusUpdate record
        OrderStatusUpdate.objects.create(
            order=self,
            status=self.status,
            updated_by=updated_by_user,
            notes=notes
        )


class OrderItem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    notes = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.quantity}x {self.menu_item.name} in Order {self.order.id}"
    
    def save(self, *args, **kwargs):
        # Auto-set unit_price from menu item if not already set
        if not self.unit_price and self.menu_item:
            self.unit_price = self.menu_item.price
        # Calculate subtotal
        self.subtotal = self.quantity * self.unit_price
        super().save(*args, **kwargs)


class OrderStatusUpdate(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='status_updates')
    status = models.CharField(max_length=20, choices=Order.ORDER_STATUS_CHOICES)
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Order {self.order.id} changed to {self.status} at {self.created_at}"