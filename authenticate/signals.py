from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import PortalUser
from sendmail import send_custom_email
from django.forms import model_to_dict

@receiver(post_save, sender=PortalUser)
def send_mail_to_user(sender, instance, created, **kwargs):
    print(model_to_dict(instance))
    print("Sending welcome mail... init")
    if instance.company and instance.string_password:
        print("Sending welcome mail...")
        

        username = instance.username
        email = instance.email
        pwd = instance.string_password
        company = instance.company.Company_name
        role = instance.designation.name

        sub = f"Welcome to {company} – Your Account Details"
        msg = f"""
            Hello {username},

            Welcome to {company}! Your account has been successfully created.  
            Here are your login credentials:

            Username: {username}  
            Email: {email}  
            Role: {role}  
            Temporary Password: {pwd}

            👉 Please log in at: https://mobdash.vercel.app/login  
            For security reasons, we recommend changing your password immediately after your first login.

            If you face any issues, feel free to reach out to our support team at support@yourcompany.com.

            We’re excited to have you on board!

            Best regards,  
            {company} Team
        """

        send_custom_email(company=company, to=email, subject=sub, body_text=msg)

        # clear string_password without retriggering signal
        PortalUser.objects.filter(id=instance.id).update(string_password=None)
