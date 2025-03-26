from django.db import models
from OnBoard.Company.models import Company
from OnBoard.Organization.models import Organizations
from Dashboard.ModelsByPage.DashAdmin import Vendors

class viewPaperBill(models.Model):
    account_number = models.CharField(max_length=255, null=False)
    wireless_number = models.CharField(max_length=255, null=True, blank=True)
    invoice_number = models.CharField(max_length=255, null=False)
    user_name = models.CharField(max_length=255, null=True, blank=True)
    invoice_date = models.CharField(max_length=255, null=True, blank=True)
    due_date = models.CharField(max_length=255, null=True, blank=True)
    monthly_bill = models.CharField(max_length=255, null=True, blank=True)

    company = models.ForeignKey(
        Company, related_name='company_view_paper_bills', on_delete=models.CASCADE, default=None, null=True, blank=True
    )
    organization = models.ForeignKey(
        Organizations, related_name='organization_view_paper_bills', on_delete=models.CASCADE, default=None
    )
    vendor = models.ForeignKey(
        Vendors, related_name='vendor_view_paper_bills', on_delete=models.CASCADE, default=None
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'ViewPaperBill'
    
    def __str__(self):
        return f'{self.company.Company_name} - {self.organization.Organization_name} - {self.vendor.name} - {self.account_number} - {self.wireless_number}'

# Create your models here.
class ViewUploadBill(models.Model):
    file_type = models.CharField(max_length=255, null=False)
    file = models.FileField(upload_to='ViewUploadedBills/')
    company = models.ForeignKey(
        Company, related_name='company_view_upload_bills', on_delete=models.CASCADE, default=None, null=True, blank=True
    )
    organization = models.ForeignKey(
        Organizations, related_name='organization_view_upload_bills', on_delete=models.CASCADE, default=None
    )
    vendor = models.ForeignKey(
        Vendors, related_name='vendor_view_upload_bills', on_delete=models.CASCADE, default=None
    )
    month = models.CharField(max_length=255, null=False)
    year = models.IntegerField(null=False)

    types = models.CharField(max_length=255, null=True, blank=True)



    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    output_file = models.FileField(upload_to='ViewUploadedBills/', null=True, blank=True)

    class Meta:
        db_table = 'ViewUploadBill'

    def __str__(self):
        return f'{self.file_type} - {self.company} - {self.organization} - {self.vendor} - {self.month} - {self.year}'
    

class ProcessedWorkbook(models.Model):
    uploadbill = models.ForeignKey(ViewUploadBill, related_name='processed_work', on_delete=models.CASCADE, null=True, blank=True)
    account_number = models.CharField(max_length=255)
    vendor_name = models.CharField(max_length=255)
    company_name = models.CharField(max_length=255, blank=True, null=True)
    sub_company_name = models.CharField(max_length=255, blank=True, null=True)
    workbook_name = models.CharField(max_length=255)
    workbook_data = models.BinaryField()
    bill_date_info = models.CharField(max_length=255, blank=True, null=True)
    output_file = models.FileField(upload_to='ViewUploadedBills/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'ProcessedWorkbook'

    def __str__(self):
        return f'{self.account_number} - {self.vendor_name} - {self.company_name} - {self.sub_company_name} - {self.workbook_name}'


from OnBoard.Ban.models import UploadBAN, BaseDataTable


class Contracts(models.Model):
    baseban = models.ForeignKey(BaseDataTable, related_name='base_ban_contracts', on_delete=models.CASCADE, null=True, blank=True)
    uploadedban = models.ForeignKey(UploadBAN, related_name='uploaded_ban_contracts', on_delete=models.CASCADE, null=True, blank=True)
    person = models.CharField(max_length=255, null=True, blank=True)
    term = models.CharField(max_length=255, null=True, blank=True)
    status = models.CharField(max_length=255, null=True, blank=True)
    notes = models.CharField(max_length=255, null=True, blank=True)
    contract_file = models.FileField(upload_to='BanContracts/', null=True, blank=True)
    contract_name = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    class Meta:
        db_table = 'Contracts'
    
    def __str__(self):
        return f'Contract for {self.baseban.accountnumber if self.baseban else self.uploadedban.account_number}'