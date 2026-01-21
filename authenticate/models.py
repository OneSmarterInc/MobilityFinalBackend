from django.db import models
from django.contrib.auth.models import AbstractUser
from Dashboard.ModelsByPage.DashAdmin import UserRoles
from OnBoard.Company.models import Company
from django.contrib.auth.hashers import make_password, is_password_usable
from OnBoard.Organization.models import Organizations
from Dashboard.ModelsByPage.DashAdmin import Vendors
from addon import normalize_us_phone
# Create your models here.

class PortalUser(AbstractUser):
    email = models.EmailField(unique=True)
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
    is_admin = models.BooleanField(default=False)
    is_notified = models.BooleanField(default=False)
    class Meta:
        db_table = "PortalUser"

    def save(self, *args, **kwargs):
        # Encrypt only if it's not already hashed
        if self.phone_number: self.phone_number = normalize_us_phone(self.phone_number)
        if self.mobile_number: self.mobile_number = normalize_us_phone(self.mobile_number)
        if self.temp_password and not self.temp_password.startswith("pbkdf2_"):
            self.temp_password = make_password(self.temp_password)

        self.is_admin = not self.vendor and not self.account_number
        
        super().save(*args, **kwargs)


    def __str__(self):
        return f'{self.email}'
    
class EmployeeWirelessNumber(models.Model):
    user = models.ForeignKey(
        PortalUser,
        related_name="wireless_numbers",
        on_delete=models.CASCADE
    )
    number = models.CharField(max_length=20, unique=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "EmployeeWirelessNumber"

    def __str__(self):
        return self.number

class UserLogs(models.Model):
    organization = models.ForeignKey(Organizations, on_delete=models.CASCADE, null=True, blank=True)
    user = models.ForeignKey(PortalUser, on_delete=models.CASCADE)
    description = models.TextField(db_index=True)
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