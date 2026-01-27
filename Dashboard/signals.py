from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
import json

from authenticate.models import PortalUser
from sendmail import send_custom_email
from addon import parse_until_dict

from .ModelsByPage.DashAdmin import Vendors
from .ModelsByPage.cat import BaselineCategories
from .ModelsByPage.Req import Requests, TrackingInfo, upgrade_device_request, AccessoriesRequest
from Dashboard.ModelsByPage.DashAdmin import UserRoles
from OnBoard.Ban.models import BaselineDataTable, UniquePdfDataTable


# =========================
# EMAIL HELPERS (US-SAFE)
# =========================



def notify_user(email, subject, body, company):
    send_custom_email(to=email, subject=subject, body_text=body, company=company)


def notify_admins(admins, subject, body, company):
    if admins:
        send_custom_email(
            to=list(admins.values_list("email", flat=True)),
            subject=subject,
            body_text=body,
            company=company
        )


# =========================
# UPGRADE DEVICE REQUEST
# =========================

@receiver(post_save, sender=upgrade_device_request)
def send_upgrade_device_status(sender, instance, created, **kwargs):
    try:
        requester = instance.raised_by
        requester_org = instance.sub_company.Organization_name
        company = instance.sub_company.company.Company_name

        admins = PortalUser.objects.filter(organization=requester.organization,
        ).filter(vendor=None,account_number=None)

        print("wireless",instance.wireless_number)
        print(instance.authority_status)

        if created:
            subject = "Device Upgrade Request Submitted"
            body = (
                f"Hello {requester.first_name},\n\n"
                f"Your request to upgrade your device has been successfully submitted to {requester_org} for review.\n\n"
                "You will be notified once a decision has been made.\n\n"
                f"Regards,\n{requester_org} Support Team"
            )

        if instance.status == "Rejected":
            subject = "Device Upgrade Request Rejected"
            body = (
                f"Hello {requester.first_name},\n\n"
                f"Your device upgrade request was reviewed and rejected by {requester_org}.\n\n"
                "If you believe this decision is incorrect, please contact your organization administrator.\n\n"
                f"Regards,\n{requester_org} Support Team"
            )

        elif instance.status == "Approved":
            subject = "Device Upgrade Request Approved"
            body = (
                f"Hello {requester.first_name},\n\n"
                f"Your device upgrade request has been approved by {requester_org} "
                "and forwarded for final authority verification.\n\n"
                f"Regards,\n{requester_org} Support Team"
            )
        


        if instance.authority_status == "Completed":
            print("completed")
            employee = UniquePdfDataTable.objects.filter(
                viewuploaded=None,
                viewpapered=None,
                sub_company=requester_org,
                vendor=requester.vendor,
                account_number=requester.account_number,
                wireless_number=instance.wireless_number
            ).first()

            print("em==",employee)

            new_date = instance.new_upgrade_date
            if employee:
                employee.upgrade_eligible_date = new_date
                employee.save()

            subject = "Device Upgrade Request Completed"
            body = (
                f"Hello {requester.first_name},\n\n"
                "Your device upgrade request has been fully approved and completed.\n\n"
                f"The upgraded device is valid until {new_date.strftime('%d %B %Y')}.\n"
                "You will not be able to submit another upgrade request before this date.\n\n"
                f"Regards,\n{requester_org} Support Team"
            )

            notify_admins(
                admins,
                subject,
                (
                    f"The device upgrade request submitted by {requester.first_name} {requester.last_name} "
                    "has been successfully completed and verified by the company authority."
                ),
                company
            )

        else:
            return

        notify_user(requester.email, subject, body, company)

    except Exception as e:
        print(e)


# =========================
# GENERIC REQUESTS
# =========================

@receiver(post_save, sender=Requests)
def send_request_status(sender, instance, created, **kwargs):
    try:
        requester = instance.requester
        org = instance.organization.Organization_name
        company = instance.organization.company.Company_name

        admins = PortalUser.objects.filter(organization=requester.organization,
        ).filter(vendor=None,account_number=None)

        if created:
            subject = f"Request Submitted: {instance.request_type}"
            body = (
                f"Hello {requester.first_name},\n\n"
                f"Your request for {instance.request_type} has been submitted to {org} for review.\n\n"
                "You will be notified once the review is completed.\n\n"
                f"Regards,\n{org} Support Team"
            )

        elif instance.status == "Rejected":
            subject = f"Request Rejected: {instance.request_type}"
            body = (
                f"Hello {requester.first_name},\n\n"
                f"Your request for {instance.request_type} was rejected by {org}.\n\n"
                "Please contact your organization administrator if clarification is needed.\n\n"
                f"Regards,\n{org} Support Team"
            )

        elif instance.status == "Approved":
            subject = f"Request Approved: {instance.request_type}"
            body = (
                f"Hello {requester.first_name},\n\n"
                f"Your request for {instance.request_type} has been approved and forwarded "
                "for final authority processing.\n\n"
                f"Regards,\n{org} Support Team"
            )

        elif instance.authority_status == "Completed":
            subject = f"Request Completed: {instance.request_type}"
            body = (
                f"Hello {requester.first_name},\n\n"
                f"Your request for {instance.request_type} has been fully completed.\n\n"
                "No further action is required.\n\n"
                f"Regards,\n{org} Support Team"
            )

            notify_admins(
                admins,
                subject,
                f"The request submitted by {requester.first_name} {requester.last_name} has been completed.",
                company
            )

        else:
            return

        notify_user(requester.email, subject, body, company)

    except Exception as e:
        print(e)


# =========================
# ACCESSORIES REQUEST
# =========================

@receiver(post_save, sender=AccessoriesRequest)
def accessories_request_mail(sender, instance, created, **kwargs):
    try:
        requester = instance.requester
        org = instance.organization.Organization_name
        company = instance.organization.company.Company_name

        admins = PortalUser.objects.filter(organization=requester.organization,
        ).filter(vendor=None,account_number=None)

        if created:
            subject = f"{instance.request_type} Request Submitted"
            body = (
                f"Hello {requester.first_name},\n\n"
                f"Your request for {instance.accessory_type} has been submitted to {org} for review.\n\n"
                f"Regards,\n{org} Support Team"
            )

        elif instance.status == "Rejected":
            subject = f"{instance.request_type} Request Rejected"
            body = (
                f"Hello {requester.first_name},\n\n"
                f"Your request for {instance.accessory_type} was rejected by {org}.\n\n"
                f"Regards,\n{org} Support Team"
            )

        elif instance.status == "Approved":
            subject = f"{instance.request_type} Request Approved"
            body = (
                f"Hello {requester.first_name},\n\n"
                f"Your request for {instance.accessory_type} has been approved and forwarded for final processing.\n\n"
                f"Regards,\n{org} Support Team"
            )

        elif instance.authority_status == "Completed":
            subject = f"{instance.request_type} Request Completed"
            body = (
                f"Hello {requester.first_name},\n\n"
                f"Your request for {instance.accessory_type} has been completed.\n\n"
                f"Regards,\n{org} Support Team"
            )

            notify_admins(
                admins,
                subject,
                f"The accessories request submitted by {requester.first_name} has been completed.",
                company
            )

        else:
            return

        notify_user(requester.email, subject, body, company)

    except Exception as e:
        print(e)


# =========================
# TRACKING + BASELINE LOGIC
# (UNCHANGED – NO EMAILS)
# =========================

@receiver(post_save, sender=Requests)
def make_tracking_info(sender, instance, created, **kwargs):
    if created and ("cancel" in instance.request_type.lower() or "upgrade" in instance.request_type.lower()):
        TrackingInfo.objects.create(request=instance)

# Remaining baseline/category signals intentionally unchanged
