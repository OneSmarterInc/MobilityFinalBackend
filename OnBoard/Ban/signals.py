from django.db.models.signals import post_save, pre_save, post_delete,pre_delete
from django.dispatch import receiver
from .models import BaseDataTable, OnboardBan, UploadBAN, UniquePdfDataTable
from Dashboard.ModelsByPage.Req import CostCenters
from View.models import Contracts
from Batch.ser import NotificationSerializer
from detect_model_changes import detect_model_changes
from authenticate.views import saveuserlog
from authenticate.models import PortalUser, EmployeeWirelessNumber
from django.db.models import Q


@receiver(post_save, sender=UniquePdfDataTable) 
def sync_employee_wireless(sender, instance, **kwargs): 
    obj = EmployeeWirelessNumber.objects.filter( number=instance.wireless_number ).first() 
    if not obj: return 
    new_is_active = instance.User_status == "Active" 
    if obj.is_active != new_is_active: 
        obj.is_active = new_is_active 
        obj.save()


@receiver(pre_delete, sender=BaseDataTable)
def delete_ban_users(sender, instance, **kwargs):
    q = Q(account_number=instance.accountnumber)

    if instance.banOnboarded_id:
        q &= Q(
            organization_id=instance.banOnboarded.organization_id,
            vendor_id=instance.banOnboarded.vendor_id,
        )

    if instance.banUploaded_id:
        q |= Q(
            organization_id=instance.banUploaded.organization_id,
            vendor_id=instance.banUploaded.Vendor_id,
        )

    all_users = PortalUser.objects.filter(q)

    print("Users to be deleted:", all_users.count())

    all_users.delete()


@receiver(post_save, sender=BaseDataTable)
def remittance_format_after_save(sender, instance, created, **kwargs):

    if created:
        billingAdd = instance.BillingAdd
        if billingAdd:
            print("billing")
            print(billingAdd)
            addlst = billingAdd.strip().replace(',',' ').split(" ")
            addlst = [item for item in addlst if item]
            if len(addlst) <= 1:
                return
            instance.BillingZip = addlst[-1]
            instance.BillingState = addlst[-2]
            instance.BillingAdd = " ".join(addlst[0:3])
            instance.BillingCity = " ".join(addlst[3:-2])
            instance.save()
    if created and instance.banOnboarded:
        print("onboarded")
        remmitAd = instance.RemittanceAdd
        if remmitAd:
            addlst = remmitAd.strip().replace(',',' ').split(" ")
            addlst = [item for item in addlst if item]
            instance.RemittanceZip = addlst[-1]
            instance.RemittanceState = addlst[-2]
            instance.RemittanceAdd = " ".join(addlst[0:3])
            instance.RemittanceCity = " ".join(addlst[3:-2])
            instance.save()
    if created and (instance.banOnboarded or instance.banUploaded):
        print("onboarded")
        main = instance.banOnboarded or instance.banUploaded
        vendor = main.Vendor if instance.banUploaded else main.vendor
        cc = instance.CostCenter
        if cc:
            CostCenters.objects.create(sub_company=main.organization, vendor=vendor,ban=instance.accountnumber,cost_center=cc)
            instance.save()
    elif created and (instance.viewuploaded or instance.viewpapered):
        print("entered")
        onboarded = BaseDataTable.objects.filter(sub_company=instance.sub_company,vendor=instance.vendor,accountnumber=instance.accountnumber).first()

        if onboarded:
            instance.RemittanceZip = onboarded.RemittanceZip
            instance.RemittanceState = onboarded.RemittanceState
            instance.RemittanceAdd = onboarded.RemittanceAdd
            instance.RemittanceCity =  onboarded.RemittanceCity
            instance.save()

    
@receiver(post_save, sender=OnboardBan)
def contract_after_save(sender, instance, created, **kwargs):
    if created and instance.contract_file:
        data = {
            'contract_name':instance.contract_name,
            'contract_file':instance.contract_file,
            'onboardedban':instance,
            'sub_company':instance.organization.Organization_name
        }
        Contracts.objects.create(**data)
        print("Contract created successfully!")

@receiver(post_save, sender=UploadBAN)
def contract_after_save(sender, instance, created, **kwargs):
    if created and instance.contract_file:
        data = {
            'contract_name':instance.contract_name,
            'contract_file':instance.contract_file,
            'uploadedban':instance,
            'sub_company':instance.organization.Organization_name
        }
        Contracts.objects.create(**data)
        print("Contract created successfully!")

from Settings.Views.History import save_ban_history, save_wireless_history
@receiver(pre_save, sender=BaseDataTable)
def detect_changes_before_save(sender, instance, **kwargs):
    if not instance.pk and (instance.banOnboarded or instance.banUploaded):
        return

    changes = detect_model_changes(instance)
    if not changes:
        return

    if changes:
        msg = "The following fields have been updated:"
        for field_name, old_value, new_value in changes:
            msg += f" {field_name}: '{old_value}' → '{new_value}';"
        if instance.banOnboarded:
            save_ban_history(onboardID=instance.banOnboarded.id, action=msg, user="System", ban=instance.accountnumber)
        elif instance.banUploaded:
            save_ban_history(uploadID=instance.banUploaded.id, action=msg, user="System", ban=instance.accountnumber)


@receiver(pre_save, sender=UniquePdfDataTable)
def detect_changes_before_save_unique(sender, instance, **kwargs):
    if not instance.pk or not (instance.banOnboarded or instance.banUploaded):
        return

    changes = detect_model_changes(instance)
    if not changes:
        return

    msg = "The following fields have been updated:"
    for field_name, old_value, new_value in changes:
        msg += f" {field_name}: '{old_value}' → '{new_value}';"
    
    if instance.banOnboarded:
        save_wireless_history(
            onboardID=instance.banOnboarded.id, 
            action=msg, 
            user="System", 
            wn=instance.wireless_number
        )
    elif instance.banUploaded:
        save_wireless_history(
            uploadID=instance.banUploaded.id, 
            action=msg, 
            user="System", 
            wn=instance.wireless_number
        )

@receiver(post_save, sender=UniquePdfDataTable)
def detect_wireless_created(sender, instance, created, **kwargs):
    if created and (instance.banOnboarded or instance.banUploaded):
        msg = f"Wireless number {instance.wireless_number} onboarded."
        if instance.banOnboarded:
            save_wireless_history(onboardID=instance.banOnboarded.id, action=msg, user="System", wn=instance.wireless_number)
        elif instance.banUploaded:
            save_wireless_history(uploadID=instance.banUploaded.id, action=msg, user="System", wn=instance.wireless_number)