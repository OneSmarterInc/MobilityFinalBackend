# emails_verify.py
import smtplib
from contextlib import contextmanager

def verify_smtp_login(*, host, port, username, password, use_tls, use_ssl, timeout=20):
    """
    Returns (ok: bool, message: str). Does NOT send an email.
    """
    conn = None
    try:
        if use_ssl:
            conn = smtplib.SMTP_SSL(host=host, port=int(port), timeout=timeout)
            conn.ehlo()
        else:
            conn = smtplib.SMTP(host=host, port=int(port), timeout=timeout)
            conn.ehlo()
            if use_tls:
                conn.starttls()
                conn.ehlo()

        conn.login(username.strip(), password.strip())
        return True, "Authenticated successfully."
    except smtplib.SMTPAuthenticationError as e:
        code = getattr(e, "smtp_code", None)
        msg = getattr(e, "smtp_error", b"").decode(errors="ignore")
        return False, f"Authentication failed ({code}): {msg or 'Invalid username or password.'}"
    except smtplib.SMTPResponseException as e:
        return False, f"SMTP error ({e.smtp_code}): {e.smtp_error.decode(errors='ignore')}"
    except Exception as e:
        return False, f"Verification failed: Please check your settings. ({e})"
    finally:
        try:
            if conn:
                conn.quit()
        except Exception:
            pass
