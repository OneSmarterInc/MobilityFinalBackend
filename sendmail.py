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
    
# emails.py
from typing import Iterable, Optional, Union, Mapping
import mimetypes
from dataclasses import dataclass

from django.core.mail import get_connection, EmailMultiAlternatives
from django.core.files import File
from django.db.models.fields.files import FieldFile
from django.utils.text import slugify

from Batch.models import EmailConfiguration  # your model

AttachmentLike = Union[str, File, FieldFile]

@dataclass(frozen=True)
class ResolvedEmailConfig:
    company: str
    organization: Optional[str]
    sender_name: str
    sender_email: str
    smtp_host: str
    smtp_port: int
    password: str
    use_tls: bool = True        # sensible default for 587
    use_ssl: bool = False       # set True if you use 465

def _fmt_from(sender_name: Optional[str], sender_email: str) -> str:
    if sender_name and sender_name.strip():
        return f'{sender_name} <{sender_email}>'
    return sender_email

def resolve_email_config(
    *,
    company: str,
    organization: Optional[str] = None,
    override: Optional[Mapping[str, object]] = None,
) -> ResolvedEmailConfig:
    """
    Resolve configuration from DB, then apply any explicit overrides.
    Required fields: sender_email, smtp_host, smtp_port, password
    """
    qs = EmailConfiguration.objects.filter(company=company)
    if organization:
        qs = qs.filter(organization=organization)

    cfg = qs.order_by('-updated', '-created').first()
    if not cfg and not override:
        raise ValueError("No EmailConfiguration found for the given company/org, and no override provided.")

    # Base values from DB (if found)
    base = {
        "company": company,
        "organization": organization,
        "sender_name": getattr(cfg, "sender_name", None) if cfg else None,
        "sender_email": getattr(cfg, "sender_email", None) if cfg else None,
        "smtp_host": getattr(cfg, "smtp_host", None) if cfg else None,
        "smtp_port": getattr(cfg, "smtp_port", None) if cfg else None,
        "password": getattr(cfg, "password", None) if cfg else None,
        # Defaults; your model doesn't store TLS/SSL—allow override to control these
         "use_tls": getattr(cfg, "use_tls", True) if cfg else True,
         "use_ssl": getattr(cfg, "use_ssl", False) if cfg else False,
    }

    # Apply explicit overrides (e.g., {'use_ssl': True, 'smtp_port': 465})
    if override:
        base.update(override)

    # Validate and normalize
    missing = [k for k in ("sender_email", "smtp_host", "smtp_port", "password") if not base.get(k)]
    if missing:
        raise ValueError(f"Missing required email config fields: {', '.join(missing)}")

    try:
        port = int(base["smtp_port"])
    except (TypeError, ValueError):
        raise ValueError("smtp_port must be an integer.")

    # --- Step B: normalize mismatches here ---
    use_tls = bool(base.get("use_tls", True))
    use_ssl = bool(base.get("use_ssl", False))

    if port == 465:
        use_ssl, use_tls = True, False
    elif port == 587:
        use_tls, use_ssl = True, False

    if use_tls and use_ssl:
        # prefer based on port; default to TLS if not 465
        if port == 465:
            use_tls = False
        else:
            use_ssl = False
    # --- end Step B ---

    return ResolvedEmailConfig(
        company=base["company"],
        organization=base["organization"],
        sender_name=base.get("sender_name") or "",
        sender_email=str(base["sender_email"]),
        smtp_host=str(base["smtp_host"]),
        smtp_port=port,
        password=str(base["password"]),
        use_tls=use_tls,
        use_ssl=use_ssl,
    )

def send_custom_email(
    *,
    company: str,
    organization: Optional[str] = None,
    subject: str,
    to: Union[str, Iterable[str]],
    body_text: Optional[str] = None,
    body_html: Optional[str] = None,
    attachments: Optional[Iterable[AttachmentLike]] = None,
    reply_to: Optional[Iterable[str]] = None,
    cc: Optional[Iterable[str]] = None,
    bcc: Optional[Iterable[str]] = None,
    headers: Optional[dict] = None,
    timeout: int = 20,
    config_override: Optional[Mapping[str, object]] = None,
    fail_silently: bool = False,
) -> bool:
    if not to:
        return
    """
    Per-company/org email sender.
    - Looks up EmailConfiguration, then applies `config_override` (wins on conflicts).
    - Supports text + HTML, multi-recipients, multi-attachments.
    """
    cfg = resolve_email_config(company=company, organization=organization, override=config_override)

    from_email = _fmt_from(cfg.sender_name, cfg.sender_email)
    to_list = [to] if isinstance(to, str) else list(to)
    text_part = body_text or (body_html and "This email contains HTML content.") or ""

    # Build connection for this send only
    connection = get_connection(
        backend='django.core.mail.backends.smtp.EmailBackend',
        host=cfg.smtp_host,
        port=cfg.smtp_port,
        username=cfg.sender_email,
        password=cfg.password,
        use_tls=cfg.use_tls,
        use_ssl=cfg.use_ssl,
        timeout=timeout,
    )

    message = EmailMultiAlternatives(
        subject=subject,
        body=text_part,
        from_email=from_email,
        to=to_list,
        cc=list(cc) if cc else None,
        bcc=list(bcc) if bcc else None,
        reply_to=list(reply_to) if reply_to else None,
        headers=headers or None,
        connection=connection,
    )
    if body_html:
        message.attach_alternative(body_html, "text/html")

    # Attach files
    def _attach(item: AttachmentLike):
        if isinstance(item, str):
            message.attach_file(item)
            return
        f: Union[File, FieldFile] = item
        need_close = False
        if getattr(f, "closed", True):
            f.open("rb")
            need_close = True
        try:
            file_name = f.name.split("/")[-1]
            content = f.read()
            mime_type, _ = mimetypes.guess_type(file_name)
            message.attach(file_name, content, mime_type or "application/octet-stream")
        finally:
            try:
                f.seek(0)
            except Exception:
                pass
            if need_close:
                f.close()

    if attachments:
        for a in attachments:
            _attach(a)

    try:
        sent = message.send(fail_silently=fail_silently)
        print(f"Message sent sucessfully to {to}")
        return bool(sent)
    except Exception:
        if fail_silently:
            return False
        raise

def send_generic_mail(receiver_mail, subject, body, attachment=None, *args, **kwargs):
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