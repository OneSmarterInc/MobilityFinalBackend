from django.db import models
# from ...Dashboard.ModelsByPage.DashAdmin import Vendors
from Dashboard.ModelsByPage.DashAdmin import Vendors
# from Company.models import Company
from ..Company.models import Company
from authenticate.models import PortalUser
from django.utils.timezone import now
# Create your models here.
import datetime

# Organization model

class Organizations(models.Model):
    Organization_name = models.CharField(max_length=255, unique=True)
    company = models.ForeignKey(
        Company, related_name='company_organizations', on_delete=models.CASCADE, default=None
    )
    tax_id = models.CharField(max_length=255, unique=True, null=False)
    Domain = models.CharField(max_length=255, unique=True, null=False)
    other_domains = models.CharField(max_length=255, unique=True, null=True)
    Phone = models.CharField(max_length=255, unique=True, null=False)
    Country = models.CharField(max_length=255, null=False)
    Fax = models.CharField(max_length=255, null=True, blank=True)
    DM_first_name = models.CharField(max_length=255, null=False)
    DM_last_name = models.CharField(max_length=255, null=False)
    DM_phone = models.CharField(max_length=255, null=False)
    DM_Fax_number = models.CharField(max_length=255, blank=True)
    DM_DID_number = models.CharField(max_length=255, null=False)
    DM_email = models.EmailField(max_length=255, null=False)
    title = models.CharField(max_length=255, null=True, blank=True)
    Batch_process_day = models.CharField(max_length=20, null=False)
    Sales_agent_company = models.CharField(max_length=255, null=True, blank=True)
    Sales_agent_name = models.CharField(max_length=255, null=True, blank=True)
    Billing_email = models.EmailField(max_length=255, null=True, blank=True)
    Bill_dispute_email = models.EmailField(max_length=255, null=True, blank=True)
    Bill_escalate_email = models.EmailField(max_length=255, null=True, blank=True)
    vendors = models.ManyToManyField(Vendors, related_name='organizations')
    favorite_vendors = models.ManyToManyField(Vendors, related_name='favorites', blank=True)
    notes = models.TextField(blank=True, null=True)
    contract_file = models.FileField(upload_to='contracts/', null=False)
    contract_name = models.CharField(max_length=255, null=False)
    status = models.IntegerField(null=False, blank=True, default=1)
    end_user_admin = models.CharField(max_length=255, null=True, blank=True)
    end_users = models.TextField(max_length=255, null=True, blank=True)
    end_user_billing = models.TextField(max_length=255, null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True, null=True)

    
    class Meta:
        db_table = 'Organizations'

    def __str__(self):
        return self.Organization_name
    
class Contract(models.Model):
    organization = models.ForeignKey(Organizations, on_delete=models.CASCADE, related_name='contract')
    vendor = models.ForeignKey(Vendors, on_delete=models.SET_NULL, null=True, blank=True)
    created_by = models.CharField(max_length=255, null=True, blank=True)
    term = models.CharField(max_length=255, null=True, blank=True)
    status = models.CharField(max_length=255, null=True, blank=True)
    notes = models.CharField(max_length=255, null=True, blank=True)
    contract_file = models.CharField(max_length=255, null=True, blank=True)
    contract_name = models.CharField(max_length=255, null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    class Meta:
        db_table = 'Contracts'
        constraints = [
            models.UniqueConstraint(fields=['organization','vendor'], name='unique_contract')
        ]
    
    def __str__(self):
        return f'Contract for {self.organization}'

    
class Division(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    organization = models.ForeignKey(Organizations, related_name='divisions', on_delete=models.CASCADE)
    name = models.CharField(max_length=255)

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    class Meta:
        db_table = 'Divisions'
        constraints = [
            models.UniqueConstraint(fields=['company', 'organization', 'name'], name='unique_division')
        ]
    
    def __str__(self):
        return f'{self.name}'
    

    
class Links(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    organization = models.ForeignKey(Organizations, related_name='links', on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    url = models.URLField(max_length=2000)

    username = models.CharField(max_length=255)
    password = models.CharField(max_length=255)
    remark = models.TextField(null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'Links'
        constraints = [
            models.UniqueConstraint(fields=['company', 'organization', 'name'], name='unique_link')
        ]

    def __str__(self):
        return f'{self.name} - {self.name}'