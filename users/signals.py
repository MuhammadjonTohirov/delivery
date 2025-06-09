from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import CustomUser, CustomerProfile


@receiver(post_save, sender=CustomUser)
def create_customer_profile(sender, instance, created, **kwargs):
    """
    Signal to create a customer profile for every new user.
    All users are customers by default.
    """
    if created:
        try:
            CustomerProfile.objects.create(user=instance)
        except Exception:
            pass  # Profile might already exist