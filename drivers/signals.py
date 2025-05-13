from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import DriverTask, DriverAvailability
from orders.models import Order
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=DriverTask)
def update_driver_availability_on_task_change(sender, instance, **kwargs):
    """
    Signal to update driver availability when a task status changes.
    """
    if instance.status in ['ACCEPTED', 'PICKED_UP']:
        # Set driver status to BUSY when they accept or are on a delivery
        driver = instance.driver
        availability, created = DriverAvailability.objects.get_or_create(
            driver=driver,
            defaults={'status': 'BUSY'}
        )
        
        if availability.status != 'BUSY':
            availability.status = 'BUSY'
            availability.save()
            logger.info(f"Driver {driver.user.full_name} status set to BUSY due to task {instance.id}")
    
    elif instance.status == 'DELIVERED':
        # Set driver status back to AVAILABLE when delivery is complete
        driver = instance.driver
        try:
            availability = DriverAvailability.objects.get(driver=driver)
            if availability.status == 'BUSY':
                availability.status = 'AVAILABLE'
                availability.save()
                logger.info(f"Driver {driver.user.full_name} status set to AVAILABLE after completing task {instance.id}")
        except DriverAvailability.DoesNotExist:
            pass


@receiver(post_save, sender=Order)
def update_order_on_driver_task_change(sender, instance, **kwargs):
    """
    Signal to sync order status with driver task status.
    """
    # This is a simplified example - real implementation would be more complex
    try:
        if hasattr(instance, 'driver_task'):
            driver_task = instance.driver_task
            
            # Sync order status based on driver task status
            if driver_task.status == 'PICKED_UP' and instance.status != 'ON_THE_WAY':
                instance.status = 'ON_THE_WAY'
                # Use update to avoid triggering this signal again
                Order.objects.filter(id=instance.id).update(status='ON_THE_WAY')
                logger.info(f"Order {instance.id} status synced to ON_THE_WAY from driver task")
            
            elif driver_task.status == 'DELIVERED' and instance.status != 'DELIVERED':
                instance.status = 'DELIVERED'
                # Use update to avoid triggering this signal again
                Order.objects.filter(id=instance.id).update(status='DELIVERED')
                logger.info(f"Order {instance.id} status synced to DELIVERED from driver task")
    except Exception as e:
        logger.error(f"Error syncing order status: {str(e)}")