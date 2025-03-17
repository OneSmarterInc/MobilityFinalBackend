from django.db import models
from OnBoard.Company.models import Company
from OnBoard.Organization.models import Organizations
from Dashboard.ModelsByPage.DashAdmin import Vendors

import os
import hashlib
from django.core.files.storage import default_storage

# Create your models here.
class Report_Billed_Data(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, null=True, blank=True)
    organization = models.ForeignKey(Organizations, on_delete=models.CASCADE, null=True, blank=True)
    vendor = models.ForeignKey(Vendors, on_delete=models.CASCADE, null=True, blank=True)
    Account_Number = models.CharField(max_length=100,default="", null=True,blank=True)
    Wireless_Number = models.CharField(max_length=20,default="", null=True,blank=True)
    User_Name = models.CharField(max_length=100,default="", null=True,blank=True)
    Report_Type = models.CharField(max_length=100,default="", null=True,blank=True)
    Month = models.CharField(max_length=100,default="", null=True,blank=True)
    Year = models.CharField(max_length=100,default="", null=True,blank=True)
    Voice_Plan_Usage = models.CharField(max_length=100,default="", null=True,blank=True)
    Messaging_Usage = models.CharField(max_length=100,default="", null=True,blank=True)
    Data_Usage_GB = models.CharField(max_length=100,default="", null=True,blank=True)
    File = models.FileField(upload_to='BilledData/', null=True, blank=True)
    Bill_Cycle_Date = models.CharField(max_length=100,default="", null=True,blank=True)
    created = models.DateTimeField(auto_now=True)
    updated = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        existing_record = Report_Billed_Data.objects.filter(
            company=self.company,
            organization=self.organization,
            vendor=self.vendor,
            Account_Number=self.Account_Number,
            Month=self.Month,
            Year=self.Year
        ).first()

        if existing_record:
            self.File = existing_record.File
        else:
            file_content = self.File.read()
            file_hash = hashlib.md5(file_content).hexdigest()
            self.File.seek(0) 

            ext = os.path.splitext(self.File.name)[-1]
            new_file_name = f"BilledData/{file_hash}{ext}"

            if default_storage.exists(new_file_name):
                self.File.name = new_file_name  
        super().save(*args, **kwargs)

    class Meta:
        db_table = 'ReportBilledData'

    


class Report_Unbilled_Data(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, null=True, blank=True)
    organization = models.ForeignKey(Organizations, on_delete=models.CASCADE, null=True, blank=True)
    vendor = models.ForeignKey(Vendors, on_delete=models.CASCADE, null=True, blank=True)
    Account_Number = models.CharField(max_length=100,default="", null=True,blank=True)
    Wireless_Number = models.CharField(max_length=20,default="", null=True,blank=True)
    User_Name = models.CharField(max_length=100,default="", null=True,blank=True)
    Report_Type = models.CharField(max_length=100,default="", null=True,blank=True)
    Month = models.CharField(max_length=100,default="", null=True,blank=True)
    Year = models.CharField(max_length=100,default="", null=True,blank=True)
    Week = models.CharField(max_length=100,default="", null=True,blank=True)
    Date = models.CharField(max_length=100,default="", null=True,blank=True)
    Usage = models.CharField(max_length=100,default="", null=True,blank=True)
    Device = models.CharField(max_length=100,default="", null=True,blank=True)
    Upgrade_Eligibilty_Date = models.CharField(max_length=100,default="", null=True,blank=True)
    File = models.FileField(upload_to='UnbilledData/', null=True, blank=True)
    File_Format = models.CharField(max_length=10, null=True, blank=True)

    created = models.DateTimeField(auto_now=True)
    updated = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        existing_record = Report_Unbilled_Data.objects.filter(
            company=self.company,
            organization=self.organization,
            vendor=self.vendor,
            Account_Number=self.Account_Number,
            Month=self.Month,
            Year=self.Year
        ).first()

        if existing_record:
            self.File = existing_record.File
        else:
            file_content = self.File.read()
            file_hash = hashlib.md5(file_content).hexdigest()
            self.File.seek(0) 

            ext = os.path.splitext(self.File.name)[-1]
            new_file_name = f"UnbilledData/{file_hash}{ext}"

            if default_storage.exists(new_file_name):
                self.File.name = new_file_name  
        super().save(*args, **kwargs)

    class Meta:
        db_table = 'ReportUnbilledData'

class Downloaded_reports(models.Model):
    report_type = models.CharField(max_length=255, blank=True, null=True)
    kwargs = models.JSONField(default=dict)
    file = models.FileField(upload_to='DownloadedExcelReports/')

    
    created = models.DateTimeField(auto_now=True)
    updated = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'DownloadedReports'
