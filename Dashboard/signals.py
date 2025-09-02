from django.db.models.signals import post_save
from .ModelsByPage.DashAdmin import Vendors
from .ModelsByPage.cat import BaselineCategories
from OnBoard.Ban.models import BaselineDataTable
from addon import parse_until_dict
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

@receiver(post_save,sender=BaselineDataTable)
def add_to_baselinemodel(sender, instance, created, **kwargs):
    if created and (instance.banUploaded or instance.banOnboarded) and instance.category_object:
        if instance.banUploaded:
            org = instance.banUploaded.organization
            vendor = instance.banUploaded.Vendor 
        elif instance.banOnboarded:
            org = instance.banOnboarded.organization
            vendor = instance.banOnboarded.vendor 
        co = parse_until_dict(instance.category_object)
        bc = BaselineCategories.objects.filter(organization=org, vendor=vendor, ban=instance.account_number)
        result = {category: list(subcats.keys()) for category, subcats in co.items()}
        for cat, lst in result.items():
            if bc.filter(category=cat).exists():
                obj = bc.first()
                prelst = obj.sub_categories or []
                newlst = list(set(prelst + lst)) 
                obj.sub_categories = newlst
                obj.save()
            else:
                BaselineCategories.objects.create(
                    organization=org, vendor=vendor, ban=instance.account_number,
                    category=cat, sub_categories=lst
                )

        
