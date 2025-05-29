from django.db.models import F
from django.utils import timezone
from geography.models import calculate_distance
from drivers.models import DriverAvailability, DriverLocation, DriverTask
from users.models import DriverProfile
import logging

logger = logging.getLogger(__name__)


def assign_driver_to_order(order):
    """
    Automatically assign the best available driver to an order
    """
    try:
        # Get all available drivers
        available_drivers = DriverProfile.objects.filter(
            availability__status='AVAILABLE',
            user__is_active=True
        ).select_related('user', 'availability')
        
        if not available_drivers.exists():
            logger.warning(f"No available drivers for order {order.id}")
            return None
        
        # Get drivers with recent location data
        drivers_with_location = []
        for driver in available_drivers:
            try:
                latest_location = driver.locations.latest('timestamp')
                # Only consider locations from last 10 minutes
                if (timezone.now() - latest_location.timestamp).seconds < 600:
                    drivers_with_location.append({
                        'driver': driver,
                        'location': latest_location
                    })
            except DriverLocation.DoesNotExist:
                continue
        
        if not drivers_with_location:
            logger.warning(f"No drivers with recent location data for order {order.id}")
            return None
        
        # Calculate distances and find closest driver
        restaurant_lat = order.restaurant.location_lat
        restaurant_lng = order.restaurant.location_lng
        
        if not restaurant_lat or not restaurant_lng:
            # If restaurant doesn't have coordinates, just pick first available driver
            selected_driver = drivers_with_location[0]['driver']
        else:
            closest_driver = None
            min_distance = float('inf')
            
            for driver_data in drivers_with_location:
                driver_location = driver_data['location']
                distance = calculate_distance(
                    restaurant_lat, restaurant_lng,
                    driver_location.latitude, driver_location.longitude
                )
                
                if distance < min_distance:
                    min_distance = distance
                    closest_driver = driver_data['driver']
            
            selected_driver = closest_driver
        
        if selected_driver:
            # Create driver task
            task = DriverTask.objects.create(
                driver=selected_driver,
                order=order,
                status='PENDING'
            )
            
            # Update driver availability to BUSY
            selected_driver.availability.status = 'BUSY'
            selected_driver.availability.save()
            
            logger.info(f"Assigned driver {selected_driver.user.full_name} to order {order.id}")
            return task
        
        return None
        
    except Exception as e:
        logger.error(f"Error assigning driver to order {order.id}: {str(e)}")
        return None


def find_nearby_drivers(latitude, longitude, radius_km=10):
    """
    Find all available drivers within a certain radius
    """
    try:
        # Get available drivers with recent locations
        available_drivers = DriverProfile.objects.filter(
            availability__status='AVAILABLE',
            user__is_active=True
        )
        
        nearby_drivers = []
        for driver in available_drivers:
            try:
                latest_location = driver.locations.latest('timestamp')
                # Only consider locations from last 10 minutes
                if (timezone.now() - latest_location.timestamp).seconds < 600:
                    distance = calculate_distance(
                        latitude, longitude,
                        latest_location.latitude, latest_location.longitude
                    )
                    
                    if distance <= radius_km:
                        nearby_drivers.append({
                            'driver': driver,
                            'distance_km': distance,
                            'location': latest_location
                        })
            except DriverLocation.DoesNotExist:
                continue
        
        # Sort by distance
        nearby_drivers.sort(key=lambda x: x['distance_km'])
        return nearby_drivers
        
    except Exception as e:
        logger.error(f"Error finding nearby drivers: {str(e)}")
        return []


def reassign_rejected_order(order):
    """
    Reassign order to next available driver if current driver rejects
    """
    try:
        # Get the rejected task
        rejected_task = order.driver_task
        rejected_task.status = 'REJECTED'
        rejected_task.save()
        
        # Free up the driver
        rejected_task.driver.availability.status = 'AVAILABLE'
        rejected_task.driver.availability.save()
        
        # Try to assign to a different driver
        task = assign_driver_to_order(order)
        
        if task:
            logger.info(f"Reassigned order {order.id} to driver {task.driver.user.full_name}")
        else:
            logger.warning(f"Failed to reassign order {order.id}")
            # You might want to notify admins or add to a manual assignment queue
        
        return task
        
    except Exception as e:
        logger.error(f"Error reassigning order {order.id}: {str(e)}")
        return None


def estimate_delivery_time(order):
    """
    Estimate delivery time based on restaurant prep time and distance
    """
    try:
        # Base preparation time (in minutes)
        prep_time = 15
        
        # Get average prep time from menu items if available
        menu_items = order.items.all()
        if menu_items:
            avg_prep_time = sum([
                item.menu_item.preparation_time or 15 
                for item in menu_items
            ]) / len(menu_items)
            prep_time = max(prep_time, avg_prep_time)
        
        # Delivery time based on distance (assuming 30 km/h average speed)
        delivery_distance = 5.0  # Default distance in km
        if order.delivery_lat and order.delivery_lng and order.restaurant.location_lat and order.restaurant.location_lng:
            delivery_distance = calculate_distance(
                order.restaurant.location_lat, order.restaurant.location_lng,
                order.delivery_lat, order.delivery_lng
            )
        
        # Calculate delivery time (30 km/h = 0.5 km/min)
        delivery_time = delivery_distance / 0.5
        
        # Total estimated time
        total_time = prep_time + delivery_time
        
        # Add buffer time
        buffer_time = 10
        total_time += buffer_time
        
        return int(total_time)
        
    except Exception as e:
        logger.error(f"Error estimating delivery time for order {order.id}: {str(e)}")
        return 30  # Default 30 minutes


def notify_driver_assignment(task):
    """
    Send notification to driver about new assignment (placeholder)
    """
    try:
        # This would integrate with the notifications system
        # For now, just log
        logger.info(f"Would send notification to driver {task.driver.user.full_name} for order {task.order.id}")
        
        # TODO: Create notification using notifications app
        # from notifications.models import Notification, NotificationTemplate
        # template = NotificationTemplate.objects.get(type='DRIVER_ASSIGNED')
        # Notification.objects.create(
        #     recipient=task.driver.user,
        #     template=template,
        #     title=f"New Delivery Assignment",
        #     message=f"You have been assigned order #{task.order.id}",
        #     related_order=task.order
        # )
        
    except Exception as e:
        logger.error(f"Error sending driver notification: {str(e)}")
