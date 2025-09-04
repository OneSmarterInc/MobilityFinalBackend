from django.db.models.signals import post_save
from .ModelsByPage.DashAdmin import Vendors
from .ModelsByPage.cat import BaselineCategories
from OnBoard.Ban.models import BaselineDataTable, UniquePdfDataTable
from addon import parse_until_dict
from django.dispatch import receiver
import json

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
@receiver(post_save,sender=BaselineCategories)
def reflect_to_category_object(sender, instance, created, **kwargs):
    item_category = instance.category
    item_descriptions = instance.sub_categories
    if created:    
        baselines = BaselineDataTable.objects.exclude(banOnboarded=None, banUploaded=None).filter(sub_company=instance.organization.Organization_name, vendor=instance.vendor.name, account_number=instance.ban)        
        uniqelines = UniquePdfDataTable.objects.exclude(banOnboarded=None, banUploaded=None).filter(sub_company=instance.organization.Organization_name, vendor=instance.vendor.name, account_number=instance.ban)
        for obj in baselines:
            co = parse_until_dict(obj.category_object)
            lst = co.keys()
            print(item_category, lst)
            if item_category in lst:
                subDescriptions = list(co.get(item_category).keys())
                updated = [item for item in item_descriptions if item not in subDescriptions]
                for itemDescription in updated:
                    co[item_category][itemDescription] = 0
            else:
                co[item_category] = {}
                for itemDescription in item_descriptions:
                    co[item_category][itemDescription] = 0
            obj.category_object = json.dumps(co)
            obj.save()
            uniqelines.filter(wireless_number=obj.Wireless_number).update(category_object=json.dumps(co))
    else:
        print("updated")
        # baselines = BaselineDataTable.objects.exclude(banOnboarded=None, banUploaded=None).filter(sub_company=instance.organization.Organization_name, vendor=instance.vendor.name, account_number=instance.ban)        
        # uniqelines = UniquePdfDataTable.objects.exclude(banOnboarded=None, banUploaded=None).filter(sub_company=instance.organization.Organization_name, vendor=instance.vendor.name, account_number=instance.ban)
        # for obj in baselines:
        #     co = parse_until_dict(obj.category_object)
        #     lst = co.keys()
        #     print(item_category, lst)