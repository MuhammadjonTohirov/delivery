from datetime import timedelta
from django.utils import timezone
from django.apps import apps


def cancel_timed_out_orders(timeout_minutes=20):
    """
    Cancels orders that have been in PLACED status for too long.
    
    This function would typically be called by a scheduled task (Celery, cron).
    It finds all orders in PLACED status that were created more than
    timeout_minutes ago and cancels them.
    
    Args:
        timeout_minutes: Number of minutes to wait before auto-cancelling orders
    
    Returns:
        int: Number of orders cancelled
    """
    # Use apps.get_model to avoid circular imports
    Order = apps.get_model('orders', 'Order')
    # No need to import OrderStatusUpdate if the model method handles it.
    
    cutoff_time = timezone.now() - timedelta(minutes=timeout_minutes)
    
    # Find orders that are still in PLACED status and older than the cutoff
    orders_to_cancel = Order.objects.filter(
        status='PLACED',
        created_at__lt=cutoff_time
    )
    
    cancelled_count = 0
    
    # Cancel each order
    for order in orders_to_cancel:
        # Use the new update_status method.
        # Pass None for updated_by_user, as this is a system action.
        # The Order.update_status method will create the OrderStatusUpdate record.
        order.update_status(
            new_status='CANCELLED',
            updated_by_user=None, 
            notes='Automatically cancelled due to restaurant inactivity.'
        )
        cancelled_count += 1
            
    return cancelled_count