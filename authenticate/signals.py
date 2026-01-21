from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import PortalUser,EmployeeWirelessNumber
from sendmail import send_custom_email, send_generic_mail
from OnBoard.Ban.models import UniquePdfDataTable
from django.forms import model_to_dict
from Batch.models import EmailConfiguration
@receiver(post_save, sender=EmployeeWirelessNumber) 
def sync_unique(sender, instance, **kwargs): 
    obj= UniquePdfDataTable.objects.filter( wireless_number=instance.number ).first() 
    if not obj: return 
    print("sync unique") 
    new_status = "Active" if instance.is_active else "Inactive" 
    if obj.User_status != new_status: 
        obj.User_status = new_status 
        obj.save()


@receiver(post_save, sender=PortalUser)
def send_mail_to_user(sender, instance, created, **kwargs):

    if created:
        _check = EmployeeWirelessNumber.objects.filter(number=instance.mobile_number).exists()
        print(_check,instance.vendor,instance.account_number,instance.mobile_number)
        if not _check and instance.account_number:
            EmployeeWirelessNumber.objects.create(user=instance,number=instance.mobile_number)
            print("wireless_created",instance.email,instance.mobile_number)

        UserSignalThread(
            instance=instance,
            company=instance.company.Company_name if instance.company else None,
            organization=instance.organization.Organization_name if instance.organization else None,
            role=instance.designation.name if instance.designation else None,
            username=instance.username,
            email=instance.email,
            pwd=instance.string_password
        ).start()
        

import threading
import os
class UserSignalThread(threading.Thread):
    def __init__(self, instance, company, organization, role, username, email, pwd):
        self.instance = instance
        self.username = username
        self.email = email
        self.pwd = pwd
        self.company = company
        self.organization = organization
        self.role = role
        threading.Thread.__init__(self)

    def run(self):
        try:
            if self.company and self.instance.organization and self.instance.string_password:
                print("Sending welcome mail...")
                
                sub = f"Welcome to {self.organization} – Your Account Details"
                print(self.role)
                if not (self.instance.vendor and self.instance.account_number):
                    msg = f"""
                        Hello {self.username},

                        Welcome to {self.organization}! Your account has been successfully created.

                        Here are your login credentials:
                        - Email: {self.email}
                        - Role: {self.role}
                        - Temporary Password: {self.pwd}

                        👉 Login here: https://mobdash.vercel.app/login  
                        For security reasons, please change your password immediately after your first login.

                        ⚠️ **Priority Setup Tasks (Action Required)**
                        To ensure smooth operations, please complete the following tasks as soon as possible:
                        1. Configure Email settings : https://mobdash.vercel.app/dashboard/email-configurations
                        2. Add Contacts : https://mobdash.vercel.app/dashboard/manageProfile
                        3. Complete the Organization Profile : https://mobdash.vercel.app/onboard/organizationDetails/OSI

                        These steps are mandatory to fully activate and manage your organization within the system.

                        If you face any issues, reach out to our support team at support@yourcompany.com.

                        Best regards,  
                        {self.organization} Team
                    """
                    if EmailConfiguration.objects.filter(organization=self.organization).exists(): send_custom_email(company=self.company, to=self.email, subject=sub, body_text=msg)
                    else:send_generic_mail(receiver_mail=self.email, subject=sub, body=msg)

                else:
                    msg = f"""
                        Hello {self.username},

                        Welcome to {self.organization}! Your account has been successfully created.  
                        Here are your login credentials:

                        Email: {self.email}  
                        Role: {self.role}  
                        Temporary Password: {self.pwd}

                        👉 Please log in at: https://mobdash.vercel.app/login  
                        For security reasons, we recommend changing your password immediately after your first login.

                        If you face any issues, feel free to reach out to our support team at support@yourcompany.com.

                        We’re excited to have you on board!

                        Best regards,  
                        {self.organization} Team
                    """

                    send_custom_email(company=self.company, to=self.email, subject=sub, body_text=msg)

                # clear string_password without retriggering signal
                self.instance.is_notified = True
                self.instance.string_password = None
                self.instance.save()
        except Exception as e:
            print(f"❌ Portal User signal failed: {e} {self.instance}")
            return False, e
        
