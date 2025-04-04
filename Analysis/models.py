from django.db import models
from OnBoard.Company.models import Company
from authenticate.models import PortalUser

from Dashboard.ModelsByPage.DashAdmin import Vendors
# Create your models here.

class Analysis(models.Model):
    company = models.ForeignKey(
        Company, related_name='companyanalysis', on_delete=models.CASCADE, default=None, null=True, blank=True
    )
    vendor = models.ForeignKey(
        Vendors, related_name='vendoranalysis', on_delete=models.CASCADE, default=None
    )
    client = models.CharField(max_length=255, null=False, blank=False)
    remark = models.TextField(max_length=255, null=True, blank=True)
    uploadBill = models.FileField(upload_to='BillAnalysis/')
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(PortalUser, related_name='analysisby', on_delete=models.SET_NULL, null=True, blank=True)
    bill_date_info = models.CharField(max_length=255, null=True, blank=True)
    excel = models.FileField(upload_to='BillAnalysis/', null=True, blank=True)
    is_processed = models.BooleanField(default=False)
    class Meta:
        db_table = 'Analysis'
    
    def __str__(self):
        return f'{self.vendor} - {self.uploadBill} - {self.client}'



