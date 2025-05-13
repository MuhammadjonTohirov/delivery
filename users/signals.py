from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import CustomUser, CustomerProfile, DriverProfile, RestaurantProfile


@receiver(post_save, sender=CustomUser)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Signal to create the appropriate profile when a user is created.
    """
    if created:
        if instance.role == 'CUSTOMER' and not CustomerProfile.objects.filter(user=instance).exists():
            CustomerProfile.objects.create(user=instance)
        elif instance.role == 'DRIVER' and not DriverProfile.objects.filter(user=instance).exists():
            DriverProfile.objects.create(user=instance)
        elif instance.role == 'RESTAURANT' and not RestaurantProfile.objects.filter(user=instance).exists():
            RestaurantProfile.objects.create(
                user=instance,
                business_name=f"{instance.full_name}'s Restaurant"
            )