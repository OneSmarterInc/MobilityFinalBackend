from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import BaseDataTable, OnboardBan, UploadBAN, UniquePdfDataTable
from Dashboard.ModelsByPage.Req import CostCenters
from View.models import Contracts
from Batch.ser import NotificationSerializer
@receiver(post_save, sender=BaseDataTable)
def remittance_format_after_save(sender, instance, created, **kwargs):

    if created:
        billingAdd = instance.BillingAdd
        if billingAdd:
            print("billing")
            addlst = billingAdd.strip().replace(',',' ').split(" ")
            addlst = [item for item in addlst if item]
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
    if instance.pk and (instance.banOnboarded or instance.banUploaded):
        old_instance = sender.objects.get(pk=instance.pk)

        changed_fields = []
        for field in instance._meta.fields:
            field_name = field.name
            old_value = getattr(old_instance, field_name) 
            old_value = None if old_value in (None,"") else old_value
            new_value = getattr(instance, field_name)
            new_value = None if new_value in (None,"") else new_value
            if old_value != new_value:
                changed_fields.append((field_name, old_value, new_value))

        if changed_fields:
            msg = "The following fields have been updated:"
            print("Changes detected:", changed_fields)
            for field_name, old_value, new_value in changed_fields:
                msg += f" {field_name}: '{old_value}' → '{new_value}';"
            print(msg)
            if instance.banOnboarded:
                save_ban_history(onboardID=instance.banOnboarded.id, action=msg, user="System", ban=instance.accountnumber)
            elif instance.banUploaded:
                save_ban_history(uploadID=instance.banUploaded.id, action=msg, user="System", ban=instance.accountnumber)

    else:
        print("New record being created!")

@receiver(pre_save, sender=UniquePdfDataTable)
def detect_changes_before_save_unique(sender, instance, **kwargs):
    if instance.pk and (instance.banOnboarded or instance.banUploaded):
        old_instance = sender.objects.get(pk=instance.pk)

        changed_fields = []
        for field in instance._meta.fields:
            field_name = field.name
            old_value = getattr(old_instance, field_name) 
            old_value = None if old_value in (None,"") else old_value
            new_value = getattr(instance, field_name)
            new_value = None if new_value in (None,"") else new_value
            if old_value != new_value:
                changed_fields.append((field_name, old_value, new_value))

        if changed_fields:
            msg = "The following fields have been updated:"
            print("Changes detected:", changed_fields)
            for field_name, old_value, new_value in changed_fields:
                msg += f" {field_name}: '{old_value}' → '{new_value}';"
            print(msg)
            if instance.banOnboarded:
                save_wireless_history(onboardID=instance.banOnboarded.id, action=msg, user="System", wn=instance.wireless_number)
            elif instance.banUploaded:
                save_wireless_history(uploadID=instance.banUploaded.id, action=msg, user="System", wn=instance.wireless_number)

@receiver(post_save, sender=UniquePdfDataTable)
def detect_wireless_created(sender, instance, created, **kwargs):
    if created and (instance.banOnboarded or instance.banUploaded):
        msg = f"Wireless number {instance.wireless_number} onboarded."
        if instance.banOnboarded:
            save_wireless_history(onboardID=instance.banOnboarded.id, action=msg, user="System", wn=instance.wireless_number)
        elif instance.banUploaded:
            save_wireless_history(uploadID=instance.banUploaded.id, action=msg, user="System", wn=instance.wireless_number)