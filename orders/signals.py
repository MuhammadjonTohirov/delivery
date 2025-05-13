from django.db.models.signals import pre_save
from django.dispatch import receiver
from .models import Order, OrderStatusUpdate
import logging

logger = logging.getLogger(__name__)


@receiver(pre_save, sender=Order)
def track_order_status_change(sender, instance, **kwargs):
    """
    Signal to track order status changes.
    """
    if instance.pk:  # Only for existing orders
        try:
            old_order = Order.objects.get(pk=instance.pk)
            if old_order.status != instance.status:
                logger.info(f"Order {instance.pk} status changed from {old_order.status} to {instance.status}")
                
                # Note: We don't create OrderStatusUpdate here because it should be
                # explicitly created in the views to capture who made the change and any notes
        except Order.DoesNotExist:
            pass  # This is a new order being created