from django.db.models.signals import post_save,post_delete
from .ModelsByPage.DashAdmin import Vendors
from .ModelsByPage.cat import BaselineCategories
from OnBoard.Ban.models import BaselineDataTable, UniquePdfDataTable
from addon import parse_until_dict
from django.dispatch import receiver
from Dashboard.ModelsByPage.DashAdmin import UserRoles
from authenticate.models import PortalUser
import json
from Dashboard.ModelsByPage.Req import Requests, upgrade_device_request, AccessoriesRequest
from sendmail import send_custom_email

@receiver(post_save, sender=upgrade_device_request)
def send_upgrade_device_status(sender, instance, created, **kwargs):
    try:
        requester = instance.raised_by
        requester_mail = requester.email
        requester_name = f"{requester.first_name} {requester.last_name}" or requester.username
        admins = PortalUser.objects.filter(
            organization=requester.organization,
            designation__name__in=["Client Admin"]
        )
        print(admins.values_list("email", flat=True))
        requester_org = instance.sub_company.Organization_name
        if created:
            sub = f"Request to upgrade device created"
            msg = (
                f"Dear {requester.first_name},\n\n"
                f"Your request to upgrade your device has been successfully created and submitted to {requester_org} for review.\n\n"
                f"Our team will notify you once it has been reviewed by your organization or approved by the authority.\n\n"
                f"Best regards,\n"
                f"The {requester_org} Support Team"
            )
        else:
            if instance.status == "Rejected":
                sub = f"Request Rejected"
                msg = (
                    f"Dear {requester.first_name},\n\n"
                    f"Your request to upgrade your device has been rejected by your organization ({requester_org}).\n\n"
                    f"If you believe this was in error, please contact your organization administrator for clarification.\n\n"
                    f"Regards,\n"
                    f"The {requester_org} Support Team"
                )

            elif instance.status == "Approved":
                sub = f"Request Approved by Organization"
                msg = (
                    f"Dear {requester.first_name},\n\n"
                    f"Good news! Your request to upgrade your device has been approved by your organization ({requester_org}).\n\n"
                    f"It will now be processed and verified by the company authority for final completion.\n\n"
                    f"Regards,\n"
                    f"The {requester_org} Support Team"
                )

            elif instance.authority_status == "Completed":
                sub = f"Request Completed by Authority"
                msg = (
                    f"Dear {instance.requester.first_name},\n\n"
                    f"We are pleased to inform you that your request to upgrade your device has been completed and verified by the company authority.\n\n"
                    f"Thank you for your patience and cooperation.\n\n"
                    f"Regards,\n"
                    f"The {requester_org} Support Team"
                )
                if admins:
                    msg = (
                        f"Dear {requester_org} Team,\n\n"
                        f"This is to inform you that the request submitted by {requester_name} "
                        f"to upgrade users device has been successfully completed and verified by the company authority.\n\n"
                        f"Please review the request details in your dashboard if any further action or acknowledgment is required.\n\n"
                        f"Best regards,\n"
                        f"The Company Authority\n"
                        f"(Automated Notification)"
                    )
                    send_custom_email(to=list(admins.values_list("email", flat=True)), subject=sub, body_text=msg, company=instance.organization.company.Company_name)

            else:
                sub = None
                msg = None
        if sub and msg: send_custom_email(to=requester_mail, subject=sub, body_text=msg, company=instance.sub_company.company.Company_name)
        
    except Exception as e:
        print(e)
    

@receiver(post_save, sender=Requests)
def send_mail(sender, instance, created, **kwargs):

    try:
        requester = instance.requester
        requester_mail = requester.email
        requester_name = f"{requester.first_name} {requester.last_name}" or requester.username
        admins = PortalUser.objects.filter(
            organization=requester.organization,
            designation__name__in=["Client Admin"]
        )
        print(admins.values_list("email", flat=True))
        requester_org = instance.organization.Organization_name

        if created:
            sub = f"Request Created: {instance.request_type}"
            msg = (
                f"Dear {requester.first_name},\n\n"
                f"Your request for {instance.request_type} has been successfully created and submitted to {requester_org} for review.\n\n"
                f"Our team will notify you once it has been reviewed by your organization or approved by the authority.\n\n"
                f"Best regards,\n"
                f"The {requester_org} Support Team"
            )

        else:
            if instance.status == "Rejected":
                sub = f"Request Rejected: {instance.request_type}"
                msg = (
                    f"Dear {requester.first_name},\n\n"
                    f"Your request for {instance.request_type} has been rejected by your organization ({requester_org}).\n\n"
                    f"If you believe this was in error, please contact your organization administrator for clarification.\n\n"
                    f"Regards,\n"
                    f"The {requester_org} Support Team"
                )

            elif instance.status == "Approved":
                sub = f"Request Approved by Organization: {instance.request_type}"
                msg = (
                    f"Dear {requester.first_name},\n\n"
                    f"Good news! Your request for {instance.request_type} has been approved by your organization ({requester_org}).\n\n"
                    f"It will now be processed and verified by the company authority for final completion.\n\n"
                    f"Regards,\n"
                    f"The {requester_org} Support Team"
                )

            elif instance.authority_status == "Completed":
                sub = f"Request Completed by Authority: {instance.request_type}"
                msg = (
                    f"Dear {instance.requester.first_name},\n\n"
                    f"We are pleased to inform you that your request for {instance.request_type} has been completed and verified by the company authority.\n\n"
                    f"Thank you for your patience and cooperation.\n\n"
                    f"Regards,\n"
                    f"The {requester_org} Support Team"
                )
                if admins:
                    msg = (
                        f"Dear {requester_org} Team,\n\n"
                        f"This is to inform you that the request submitted by **{requester_name}** "
                        f"for **{instance.request_type}** has been successfully **completed and verified by the company authority**.\n\n"
                        f"Please review the request details in your dashboard if any further action or acknowledgment is required.\n\n"
                        f"Best regards,\n"
                        f"The Company Authority\n"
                        f"(Automated Notification)"
                    )
                    send_custom_email(to=list(admins.values_list("email", flat=True)), subject=sub, body_text=msg, company=instance.organization.company.Company_name)

            else:
                sub = None
                msg = None

        if sub and msg: send_custom_email(to=requester_mail, subject=sub, body_text=msg, company=instance.organization.company.Company_name)
    except Exception as e:
        print(e)
        

@receiver(post_save, sender=AccessoriesRequest)
def Accessories_mail_sender(sender, instance, created, **kwargs):

    try:
        requester = instance.requester
        requester_mail = requester.email
        requester_name = f"{requester.first_name} {requester.last_name}" or requester.username
        admins = PortalUser.objects.filter(
            organization=requester.organization,
            designation__name__in=["Client Admin"]
        )
        print(admins.values_list("email", flat=True))
        requester_org = instance.organization.Organization_name

        if created:
            sub = f"Request Created: {instance.request_type}"
            msg = (
                f"Dear {requester.first_name},\n\n"
                f"Your {instance.request_type} request for {instance.accessory_type} has been successfully created and submitted to {requester_org} for review.\n\n"
                f"Our team will notify you once it has been reviewed by your organization or approved by the authority.\n\n"
                f"Best regards,\n"
                f"The {requester_org} Support Team"
            )

        else:
            if instance.status == "Rejected":
                sub = f"Request Rejected: {instance.request_type}"
                msg = (
                    f"Dear {requester.first_name},\n\n"
                    f"Your {instance.request_type} request for {instance.accessory_type} has been rejected by your organization ({requester_org}).\n\n"
                    f"If you believe this was in error, please contact your organization administrator for clarification.\n\n"
                    f"Regards,\n"
                    f"The {requester_org} Support Team"
                )

            elif instance.status == "Approved":
                sub = f"Request Approved by Organization: {instance.request_type}"
                msg = (
                    f"Dear {requester.first_name},\n\n"
                    f"Good news! Your {instance.request_type} request for {instance.accessory_type} has been approved by your organization ({requester_org}).\n\n"
                    f"It will now be processed and verified by the company authority for final completion.\n\n"
                    f"Regards,\n"
                    f"The {requester_org} Support Team"
                )

            elif instance.authority_status == "Completed":
                sub = f"Request Completed by Authority: {instance.request_type}"
                msg = (
                    f"Dear {instance.requester.first_name},\n\n"
                    f"We are pleased to inform you that your {instance.request_type} request for {instance.accessory_type} has been completed and verified by the company authority.\n\n"
                    f"Thank you for your patience and cooperation.\n\n"
                    f"Regards,\n"
                    f"The {requester_org} Support Team"
                )
                if admins:
                    msg = (
                        f"Dear {requester_org} Team,\n\n"
                        f"This is to inform you that the request submitted by **{requester_name}** "
                        f"for **{instance.request_type}** has been successfully **completed and verified by the company authority**.\n\n"
                        f"Please review the request details in your dashboard if any further action or acknowledgment is required.\n\n"
                        f"Best regards,\n"
                        f"The Company Authority\n"
                        f"(Automated Notification)"
                    )
                    send_custom_email(to=list(admins.values_list("email", flat=True)), subject=sub, body_text=msg, company=instance.organization.company.Company_name)

            else:
                sub = None
                msg = None

        if sub and msg: send_custom_email(to=requester_mail, subject=sub, body_text=msg, company=instance.organization.company.Company_name)
    except Exception as e:
        print(e)

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
        
        baselines = BaselineDataTable.objects.exclude(banOnboarded=None, banUploaded=None).filter(sub_company=instance.organization.Organization_name, vendor=instance.vendor.name, account_number=instance.ban)        
        uniqelines = UniquePdfDataTable.objects.exclude(banOnboarded=None, banUploaded=None).filter(sub_company=instance.organization.Organization_name, vendor=instance.vendor.name, account_number=instance.ban)
        for obj in baselines:
            co = parse_until_dict(obj.category_object) or {}
            values = co.get(item_category, {})

            new_co = {
                **co, 
                item_category: {
                    item: values.get(item, 0) for item in item_descriptions
                }
            }
            serialized = json.dumps(new_co)
            obj.category_object = serialized
            obj.save()

            uniqelines.filter(wireless_number=obj.Wireless_number).update(category_object=serialized)

@receiver(post_delete, sender=BaselineCategories)
def reflect_to_category_object_on_delete(sender, instance, **kwargs):

    item_category = instance.category
    item_descriptions = instance.sub_categories
    baselines = BaselineDataTable.objects.exclude(banOnboarded=None, banUploaded=None).filter(sub_company=instance.organization.Organization_name, vendor=instance.vendor.name, account_number=instance.ban)        
    uniqelines = UniquePdfDataTable.objects.exclude(banOnboarded=None, banUploaded=None).filter(sub_company=instance.organization.Organization_name, vendor=instance.vendor.name, account_number=instance.ban)


    for obj in baselines:
        co = parse_until_dict(obj.category_object) or {}
        if item_category in co.keys():
            co.pop(item_category)
        serialized = json.dumps(co)
        obj.category_object = serialized
        obj.save()
        uniqelines.filter(wireless_number=obj.Wireless_number).update(category_object=serialized)
    
