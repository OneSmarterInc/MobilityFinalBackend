from django.db.models.signals import post_save
from .ModelsByPage.DashAdmin import Vendors
from django.dispatch import receiver

@receiver(post_save, sender=Vendors)
def print_vendor_created(sender, instance, created, **kwargs):
    if created:
        print("Vendor created successfully:", instance.name, instance.created)
        print(type(instance))
