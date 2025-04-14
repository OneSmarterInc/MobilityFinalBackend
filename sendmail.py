import mimetypes
from django.core.mail import EmailMessage
from django.conf import settings
from django.core.files import File
from django.db.models.fields.files import FieldFile

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

    email.send()
