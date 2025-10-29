from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Profile

@receiver(post_save, sender=User)
def ensure_profile_exists(sender, instance, created, **kwargs):
    # Create on first save; also guard in case it was missing
    if created:
        Profile.objects.create(
            user=instance,
            full_name=instance.get_full_name() or instance.email or instance.username,
            phone="",
            address="",
            medical_license="",
        )
    else:
        # If somehow missing later, recreate
        Profile.objects.get_or_create(
            user=instance,
            defaults={
                "full_name": instance.get_full_name() or instance.email or instance.username,
                "phone": "",
                "address": "",
                "medical_license": "",
            },
        )
