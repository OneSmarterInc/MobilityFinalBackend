from celery import shared_task
import json
from sendmail import send_custom_email
from View.models import ViewUploadBill
from .newVprocessor import ProcessPdf2
from .billAnalysis import BillAnalysis
from View.enterbill.ep import EnterBillProcessExcel
from .newbillprocessor import ProcessBills


# =========================
# EMAIL TEMPLATES
# =========================

def client_upload_error_email():
    return (
        "We were unable to complete the processing of your recently submitted file "
        "due to a temporary system issue.\n\n"
        "Your data was not lost or modified. Our team is actively working on the issue.\n\n"
        "Please try submitting the file again later today. If the problem continues, "
        "reply to this email and our support team will assist you."
    )


def client_upload_success_email(filename, process_time):
    return (
        f"Your file '{filename}' has been successfully uploaded and processed.\n\n"
        f"Processing time: {process_time}\n\n"
        "No further action is required at this time."
    )


def internal_error_email(context, exception):
    return (
        f"INTERNAL ERROR — {context}\n\n"
        f"{exception}"
    )


# =========================
# BILL PDF UPLOAD
# =========================

@shared_task
def verizon_att_enterBill_processor(buffer_data, instance_id, btype):
    buffer = json.loads(buffer_data)

    company = buffer.get("company_name")
    org = buffer.get("sub_company_name")
    email = buffer.get("email")
    pdf_filename = buffer.get("pdf_filename", "").split("/")[-1]

    try:
        instance = ViewUploadBill.objects.get(id=instance_id)
    except ViewUploadBill.DoesNotExist:
        return {"message": "Upload record not found", "error": 1}

    try:
        processor = ProcessPdf2(buffer_data=buffer, instance=instance, btype=btype)
        success, msg, process_time = processor.start_process()

        process_time = (
            f"{process_time / 60:.2f} minutes"
            if process_time >= 60
            else f"{process_time:.2f} seconds"
        )

        subject = "PDF Bill Upload Update"

        if success:
            instance.is_processed = True
            instance.save()

            bill_analysis_processor.delay(buffer_data, instance_id, btype=btype)

            body = client_upload_success_email(pdf_filename, process_time)
        else:
            body = client_upload_error_email()
            if instance.pk:
                instance.delete()

        send_custom_email(
            company=company,
            organization=org,
            to=email,
            subject=subject,
            body_text=body
        )

        if not success:
            send_custom_email(
                company=company,
                organization=org,
                to="gauravdhale09@gmail.com",
                subject=subject,
                body_text=internal_error_email("PDF Bill Upload Failed", msg)
            )

    except Exception as e:
        send_custom_email(
            company=company,
            organization=org,
            to=email,
            subject="Temporary Issue During PDF Upload",
            body_text=client_upload_error_email()
        )

        send_custom_email(
            company=company,
            organization=org,
            to="gauravdhale09@gmail.com",
            subject="PDF Upload – Internal Error",
            body_text=internal_error_email("PDF Bill Upload Exception", e)
        )

        if instance.pk:
            instance.delete()


# =========================
# BILL ANALYSIS
# =========================

@shared_task
def bill_analysis_processor(buffer_data, instance_id, btype):
    buffer = json.loads(buffer_data)

    company = buffer.get("company_name")
    org = buffer.get("sub_company_name")

    try:
        instance = ViewUploadBill.objects.get(id=instance_id)
    except ViewUploadBill.DoesNotExist:
        return {"message": "Upload record not found", "error": 1}

    try:
        analysis = BillAnalysis(instance=instance, buffer_data=buffer_data, btype=btype)
        success, msg, process_time, error = analysis.process()

        if not success:
            if instance.pk:
                instance.delete()

            send_custom_email(
                company=company,
                organization=org,
                to="gauravdhale09@gmail.com",
                subject="Bill Analysis Failed",
                body_text=internal_error_email("Bill Analysis Failure", msg)
            )

    except Exception as e:
        if instance.pk:
            instance.delete()

        send_custom_email(
            company=company,
            organization=org,
            to="gauravdhale09@gmail.com",
            subject="Bill Analysis – Internal Error",
            body_text=internal_error_email("Bill Analysis Exception", e)
        )


# =========================
# VIEW BILL PROCESSORS
# =========================

@shared_task
def process_view_bills(buffer_data, instance_id):
    buffer = json.loads(buffer_data)

    try:
        instance = ViewUploadBill.objects.get(id=instance_id)
    except ViewUploadBill.DoesNotExist:
        return {"message": "Upload record not found", "error": 1}

    try:
        ProcessBills(buffer_data=buffer, instance=instance).process()
    except Exception as e:
        if instance.pk:
            instance.delete()

        send_custom_email(
            company=buffer.get("company_name"),
            to="gauravdhale09@gmail.com",
            subject="View Bill Processing Failed",
            body_text=internal_error_email("View Bill Processor", e)
        )


def process_view_excel(buffer_data, instance_id):
    buffer = json.loads(buffer_data)

    try:
        instance = ViewUploadBill.objects.get(id=instance_id)
    except ViewUploadBill.DoesNotExist:
        return {"message": "Upload record not found", "error": 1}

    try:
        EnterBillProcessExcel(buffer_data=buffer, instance=instance).process_csv_from_buffer()
    except Exception as e:
        if instance.pk:
            instance.delete()

        send_custom_email(
            company=buffer.get("company"),
            to="gauravdhale09@gmail.com",
            subject="Excel Bill Upload Failed",
            body_text=internal_error_email("Excel Bill Upload", e)
        )
