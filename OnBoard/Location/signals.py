from django.db.models.signals import pre_delete
from .models import Location
from django.dispatch import receiver
from ..Ban.models import BaseDataTable, UniquePdfDataTable, OnboardBan, UploadBAN

from django.db.models.signals import pre_delete
from django.dispatch import receiver
from django.db.models import Q

@receiver(pre_delete, sender=Location)
def update_ban_location(sender, instance, **kwargs):
    onboarded_ids = OnboardBan.objects.filter(
        location=instance
    ).values_list("id", flat=True)

    uploaded_ids = UploadBAN.objects.filter(
        location=instance
    ).values_list("id", flat=True)

    filter_condition = (
        Q(banOnboarded__in=onboarded_ids) |
        Q(banUploaded__in=uploaded_ids)
    )

    BaseDataTable.objects.filter(filter_condition).update(location=None)

    UniquePdfDataTable.objects.filter(filter_condition).update(site_name=None)
