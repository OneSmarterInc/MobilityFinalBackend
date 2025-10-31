from django.db import models
from django.contrib.auth.models import AbstractUser
from Dashboard.ModelsByPage.DashAdmin import UserRoles
from OnBoard.Company.models import Company
from django.contrib.auth.hashers import make_password, is_password_usable
from OnBoard.Organization.models import Organizations
from Dashboard.ModelsByPage.DashAdmin import Vendors
# Create your models here.

class PortalUser(AbstractUser):
    designation = models.ForeignKey(
        UserRoles,
        on_delete=models.SET_NULL,
        null=True,
        blank=True, 
        related_name="designation",
    )

    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        default=None,
        null=True,
        blank=True, 
        related_name="companyusers",  

    )

    organization = models.ForeignKey(Organizations, related_name="organization_users", on_delete=models.CASCADE, null=True, blank=True)

    vendor = models.ForeignKey(Vendors, related_name="vendor_users", on_delete=models.SET_NULL, null=True, blank=True)

    account_number = models.CharField(max_length=255, null=True, blank=True)

    string_password = models.CharField(max_length=255, null=True, blank=True)

    mobile_number = models.CharField(max_length=255, null=True, blank=True)
    phone_number = models.CharField(max_length=255, null=True, blank=True)

    contact_type = models.CharField(max_length=255, null=True, blank=True)

    temp_password = models.CharField(max_length=255, null=True, blank=True)
    class Meta:
        db_table = "PortalUser"

    def save(self, *args, **kwargs):
        # Encrypt only if it's not already hashed
        if self.temp_password and not self.temp_password.startswith("pbkdf2_"):
            self.temp_password = make_password(self.temp_password)
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.first_name} {self.last_name}'
    

class UserLogs(models.Model):
    user = models.ForeignKey(PortalUser, on_delete=models.CASCADE)
    description = models.CharField(max_length=1024, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)    

    class Meta:
        db_table = "UserLogs"

    def __str__(self):
        return f"{self.user.email} - {self.description}"

class EmailOTP(models.Model):
    user = models.OneToOneField(PortalUser, on_delete=models.CASCADE, related_name="email_otp")
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_verified = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.email} - {self.otp}"