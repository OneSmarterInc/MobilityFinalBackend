import mimetypes
from django.core.mail import EmailMessage
from django.conf import settings
from django.core.files import File
from django.db.models.fields.files import FieldFile

def send_ticket(assign_email, sub_company, vendor, account_no, title, description, priority):
    print(assign_email, sub_company, vendor, account_no, title, description, priority, ">>>>>>>>>>>>>>>>>>>>>>>>>>>.....")
    try:
        subject = title
        body = f"""
        <div> <h2>{title}</h2>
        <p>{description}</p>
        <span><b>{sub_company}</b> <br> Vendor : {vendor} <br> Account Number : {account_no} </span><br>
        <span><b>Priority</b> : {priority}</span>
        </div>
        """
        from_email = settings.DEFAULT_FROM_EMAIL  # Must be set in settings.py

        email = EmailMessage(
            subject=subject,
            body=body,
            from_email=from_email,
            to=assign_email,  
        )
        email.content_subtype = "html"  # This ensures the body is rendered as HTML
        email.send()

        print("Email sent successfully")
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False
    
def send_custom_email(receiver_mail, subject, body, attachment=None, *args, **kwargs):
    """
    Sends an email with optional file attachment.

    Supports:
    - File path (string)
    - Uploaded files (request.FILES['file'])
    - Model file fields (instance.file_field)
    """

    from_email = settings.DEFAULT_FROM_EMAIL

    email = EmailMessage(
        subject=subject,
        body=body,
        from_email=from_email,
        to=[receiver_mail],
    )

    if attachment:
        if isinstance(attachment, str):
            # File path
            email.attach_file(attachment)
        elif isinstance(attachment, FieldFile) or isinstance(attachment, File):
            # Model file field or UploadedFile
            file_name = attachment.name.split("/")[-1]
            content = attachment.read()
            mime_type, _ = mimetypes.guess_type(file_name)
            email.attach(file_name, content, mime_type or 'application/octet-stream')

    try:
        email.send()
        print(f"mail send successfully to {receiver_mail}")
    except Exception as e:
        print(e)

