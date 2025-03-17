from django.db import models
from Dashboard.ModelsByPage.DashAdmin import Vendors
from django.utils.timezone import now

class Company(models.Model):
    Company_name = models.CharField(max_length=255, unique=True, null=False)
    website = models.CharField(max_length=255, null=False, blank=True)
    Contact_number = models.CharField(max_length=255, null=False, blank=True)
    Tax_id = models.CharField(max_length=255, null=False, blank=True)
    Address = models.TextField(null=False, blank=True)
    DM_first_name = models.CharField(max_length=255, null=False)
    DM_last_name = models.CharField(max_length=255, null=False)
    DM_email = models.EmailField(max_length=255, null=False)
    DM_phone_number = models.CharField(max_length=255, null=False, default='0')
    Sales_agent_name = models.CharField(max_length=255)
    Sales_agent_details = models.TextField(max_length=255)
    notes = models.TextField(max_length=255)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True, null=True)
    Bill_payment_type = models.CharField(max_length=255, null=False)
    Bill_payment_day = models.CharField(max_length=255, null=True, blank=True)
    vendors = models.ManyToManyField(Vendors, related_name='companies')

    class Meta:
        db_table = 'Company'

    def __str__(self):
        return self.Company_name

