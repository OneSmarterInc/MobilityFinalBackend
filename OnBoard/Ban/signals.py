from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import BaseDataTable

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
    elif created and (instance.viewuploaded or instance.viewpapered):
        print("entered")
        onboarded = BaseDataTable.objects.filter(sub_company=instance.sub_company,vendor=instance.vendor,accountnumber=instance.accountnumber).first()

        if onboarded:
            instance.RemittanceZip = onboarded.RemittanceZip
            instance.RemittanceState = onboarded.RemittanceState
            instance.RemittanceAdd = onboarded.RemittanceAdd
            instance.RemittanceCity =  onboarded.RemittanceCity
            instance.save()

    
