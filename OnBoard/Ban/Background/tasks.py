from celery import shared_task
import json
from OnBoard.Ban.models import OnboardBan, InventoryUpload, BaseDataTable
from OnBoard.Ban.Background.cp import ProcessCSVOnboard
from OnBoard.Ban.Background.pp2 import ProcessPdf2
from OnBoard.Ban.Background.pp import ProcessPdf
from sendmail import send_custom_email


# =========================
# EMAIL TEMPLATES (US-SAFE)
# =========================

def client_processing_error_email():
    return (
        "We were unable to complete the processing of your recently submitted file "
        "due to a temporary system issue.\n\n"
        "Our engineering team is actively working on the resolution. "
        "Your data was not lost or modified.\n\n"
        "Please try submitting the file again later today. "
        "If the issue persists, reply to this email and our support team will assist you."
    )


def client_processing_success_email(filename, process_time):
    return (
        f"Your file '{filename}' has been successfully processed.\n\n"
        f"Processing time: {process_time}\n\n"
        "No further action is required. If you have any questions, "
        "feel free to reply to this email."
    )


def internal_error_email(exception):
    return (
        "INTERNAL ERROR DURING FILE PROCESSING\n\n"
        f"{exception}"
    )


# =========================
# PDF ONBOARD PROCESSOR
# =========================

@shared_task
def verizon_att_onboardPDF_processor(buffer_data, instance_id, btype):
    buffer = json.loads(buffer_data)

    company = buffer.get("company_name")
    org = buffer.get("sub_company")
    user_email = buffer.get("user_email")
    pdf_filename = buffer.get("pdf_filename", "").split("/")[-1]

    try:
        instance = OnboardBan.objects.get(id=instance_id)
    except OnboardBan.DoesNotExist:
        return {"message": "Onboard record not found", "error": 1}

    try:
        processor = ProcessPdf2(buffer_data=buffer, instance=instance, btype=btype)
        success, msg, process_time = processor.start_process()

        process_time = (
            f"{process_time / 60:.2f} minutes"
            if process_time >= 60
            else f"{process_time:.2f} seconds"
        )

        subject = "PDF Processing Update"

        if success:
            instance.is_processed = True
            instance.save()

            body = client_processing_success_email(pdf_filename, process_time)
        else:
            body = client_processing_error_email()
            if instance.pk:
                instance.delete()

        send_custom_email(
            company=company,
            organization=org,
            to=user_email,
            subject=subject,
            body_text=body
        )

        if not success:
            send_custom_email(
                company=company,
                organization=org,
                to="gauravdhale09@gmail.com",
                subject=subject,
                body_text=body
            )

    except Exception as e:
        subject = "Temporary Issue During PDF Processing"

        send_custom_email(
            company=company,
            organization=org,
            to=user_email,
            subject=subject,
            body_text=client_processing_error_email()
        )

        send_custom_email(
            company=company,
            organization=org,
            to="gauravdhale09@gmail.com",
            subject=subject,
            body_text=internal_error_email(e)
        )

        if instance.pk:
            instance.delete()


# =========================
# LEGACY PDF PROCESSOR
# =========================

@shared_task
def process_pdf_task(buffer_data, instance_id):
    buffer = json.loads(buffer_data)

    try:
        instance = OnboardBan.objects.get(id=instance_id)
    except OnboardBan.DoesNotExist:
        return {"message": "Onboard record not found", "error": 1}

    try:
        ProcessPdf(buffer_data=buffer, instance=instance).process_pdf_from_buffer()
    except Exception as e:
        send_custom_email(
            company=buffer.get("company_name"),
            to="gauravdhale09@gmail.com",
            subject="PDF Processing Failure",
            body_text=internal_error_email(e)
        )
        if instance.pk:
            instance.delete()


# =========================
# CSV PROCESSOR
# =========================

# @shared_task
def process_csv(instance_id, buffer_data, type=None):
    buffer = json.loads(buffer_data)

    try:
        if type == "inventory":
            instance = InventoryUpload.objects.get(id=instance_id)
        else:
            instance = BaseDataTable.objects.get(id=instance_id)
    except (InventoryUpload.DoesNotExist, BaseDataTable.DoesNotExist):
        return {"message": "Upload record not found", "error": 1}

    try:
        processor = ProcessCSVOnboard(
            buffer_data=buffer,
            instance=instance,
            uploadtype=type
        )
        return processor.process_csv_data()
    except Exception as e:
        if instance.pk:
            instance.delete()
        return {"message": str(e), "error": 1}
