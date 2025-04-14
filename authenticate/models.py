from django.db import models
from django.contrib.auth.models import AbstractUser
from Dashboard.ModelsByPage.DashAdmin import UserRoles
from OnBoard.Company.models import Company
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

    mobile_number = models.CharField(max_length=255, null=True, blank=True)
    phone_number = models.CharField(max_length=255, null=True, blank=True)

    contact_type = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        db_table = "PortalUser"

    def __str__(self):
        return self.email
    

class UserLogs(models.Model):
    user = models.ForeignKey(PortalUser, on_delete=models.CASCADE)
    description = models.CharField(max_length=1024, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)    

    class Meta:
        db_table = "UserLogs"

    def __str__(self):
        return f"{self.user.email} - {self.description}"