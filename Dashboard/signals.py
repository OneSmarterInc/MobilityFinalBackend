from django.db.models.signals import post_save
from .ModelsByPage.DashAdmin import Vendors
from django.dispatch import receiver

@receiver(post_save, sender=Vendors)
def print_vendor_created(sender, instance, created, **kwargs):
    if created:
        print("Vendor created successfully:", instance.name, instance.created)
        print(type(instance))


from .ModelsByPage.Req import Requests, TrackingInfo

@receiver(post_save,sender=Requests)
def make_tracking_info(sender, instance,created,**kwargs):
    if created and ("cancel" in instance.request_type.lower()) or ("upgrade" in instance.request_type.lower()) :
        TrackingInfo.objects.create(request=instance)
        print("tracking created!!")