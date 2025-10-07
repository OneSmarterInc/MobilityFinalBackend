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

class MultipleFileUpload(models.Model):
    company = models.ForeignKey(
        Company, related_name='companyanalysismultiple', on_delete=models.CASCADE, default=None, null=True, blank=True
    )
    vendor = models.ForeignKey(
        Vendors, related_name='vendoranalysismultiple', on_delete=models.CASCADE, default=None
    )
    client = models.CharField(max_length=255, null=False, blank=False)
    remark = models.TextField(max_length=255, null=True, blank=True)
    file1 = models.FileField(upload_to='MultipleFileUpload/', null=True, blank=True)
    file2 = models.FileField(upload_to='MultipleFileUpload/', null=True, blank=True)
    file3 = models.FileField(upload_to='MultipleFileUpload/', null=True, blank=True)
    excel = models.FileField(upload_to='BillAnalysis/', null=True, blank=True)
    is_processed = models.BooleanField(default=False)
    created_by = models.ForeignKey(PortalUser, related_name='multipleanalysisby', on_delete=models.SET_NULL, null=True, blank=True)
    savings_pdf = models.FileField(upload_to='SavingsPDF/', null=True, blank=True)

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'MultipleFileUpload'

from django.core.validators import RegexValidator
from datetime import datetime

class SummaryData(models.Model):
    multiple_analysis = models.ForeignKey(
        MultipleFileUpload,
        related_name='summary_data',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text="Reference to the uploaded file set for this analysis"
    )
    file_name = models.CharField(max_length=255, null=True, blank=True)
    account_number = models.CharField(
        max_length=255,
        help_text="Unique identifier for the customer account"
    )
    bill_date = models.CharField(
        max_length=255,
        help_text="Date of the billing cycle (e.g., 2024-09-01)"
    )
    bill_day = models.IntegerField(default=0)
    bill_month = models.IntegerField(default=0)
    bill_year = models.IntegerField(default=0)
    wireless_number = models.CharField(
        max_length=255,
        validators=[
            RegexValidator(
                regex=r'^\d{10}$',
                message="Wireless number must be exactly 10 digits",
                code="invalid_number"
            )
        ],
        help_text="10-digit wireless/phone number"
    )
    username = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="Name of the user associated with the wireless number"
    )
    data_roaming = models.CharField(
        max_length=255,
        default="NA",
        help_text="Data roaming charges for the billing cycle"
    )
    message_roaming = models.CharField(
        max_length=255,
        default="NA",
        help_text="SMS/MMS roaming charges for the billing cycle"
    )
    voice_roaming = models.CharField(
        max_length=255,
        default="NA",
        help_text="Voice call roaming charges for the billing cycle"
    )
    data_usage = models.CharField(
        max_length=255,
        default="NA",
        help_text="Total data usage (in GB) during the billing cycle"
    )
    message_usage = models.CharField(
        max_length=255,
        default="NA",
        help_text="Total number of SMS/MMS messages sent during the billing cycle"
    )
    voice_plan_usage = models.CharField(
        max_length=255,
        default="NA",
        help_text="Total voice minutes used during the billing cycle"
    )
    total_charges = models.CharField(
        max_length=255,
        default="NA",
        help_text="Grand total charges on the bill"
    )
    third_party_charges = models.CharField(max_length=255, default="NA", help_text="Third-party charges including tax")
    taxes_governmental_surcharges = models.CharField(
        max_length=255,
        default="NA",
        help_text="Taxes and government surcharges applied to the bill"
    )
    other_charges_credits = models.CharField(
        max_length=255,
        default="NA",
        help_text="Other charges or credits applied (e.g., discounts, adjustments)"
    )
    equipment_charges = models.CharField(
        max_length=255,
        default="NA",
        help_text="Charges for equipment or device installments"
    )
    usage_purchase_charges = models.CharField(
        max_length=255,
        default="NA",
        help_text="Charges for extra usage or purchases beyond the plan"
    )
    plan = models.CharField(
        max_length=255,
        default="NA",
        help_text="Name of the subscribed wireless plan"
    )
    monthly_charges = models.CharField(
        max_length=255,
        default="NA",
        help_text="Base monthly plan charges"
    )

    class Meta:
        db_table = 'SummaryData'

    # def save(self, *args, **kwargs):
    #     if self.bill_date:
    #         try:
    #             parsed_date = datetime.strptime(self.bill_date, "%b %d, %Y")
    #         except ValueError:
    #             parsed_date = datetime.strptime(self.bill_date, "%Y-%m-%d")

    #         self.bill_day = parsed_date.day
    #         self.bill_month = parsed_date.month
    #         self.bill_year = parsed_date.year
    #         # keep self.bill_date as string
    #     super().save(*args, **kwargs)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['wireless_number', 'bill_date', 'multiple_analysis'],
                name='unique_wireless_number_bill_date_id'
            )
        ]

    
from dateutil import parser


def parse_bill_date(date_str):
        try:
            return parser.parse(date_str, dayfirst=False)  # US-style month/day
        except Exception:
            raise ValueError(f"Date format not supported: {date_str}")

class AnalysisData(models.Model):
    analysis = models.ForeignKey(
        Analysis, related_name='analysisdata', on_delete=models.CASCADE, null=True, blank=True
    )
    multiple_analysis = models.ForeignKey(
        MultipleFileUpload, related_name='multipleanalysis', on_delete=models.CASCADE, null=True, blank=True
    )
    account_number = models.CharField(max_length=255, null=True, blank=True)
    bill_date = models.CharField(max_length=255, null=True, blank=True)
    bill_day = models.IntegerField(default=0)
    bill_month = models.IntegerField(default=0)
    bill_year = models.IntegerField(default=0)
    type_choices = [
        ('zero_usage', 'Zero Usage'),
        ('less_than_5_gb', 'Less than 5 GB'),
        ('between_5_and_15_gb', 'Between 5 and 15 GB'),
        ('more_than_15_gb', 'More than 15 GB'),
        ('NA_not_unlimited', 'N/A (Not Unlimited)'),
        ('NA_unlimited', 'N/A (Unlimited)'),        
    ]
    data_usage_range = models.CharField(max_length=50, choices=type_choices)
    wireless_number = models.CharField(max_length=20, null=False, blank=False)
    user_name = models.CharField(max_length=255, null=True, blank=True)
    current_plan = models.CharField(max_length=255, null=True, blank=True)
    current_plan_charges = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    current_plan_usage = models.CharField(max_length=10, default="NA")
    is_plan_recommended = models.BooleanField(default=False)
    recommended_plan = models.CharField(max_length=255, null=True, blank=True)
    recommended_plan_charges = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    recommended_plan_savings = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    file_name = models.CharField(max_length=255, null=True, blank=True)
    variance_with_last_month = models.CharField(default="NA", max_length=10)
    how_variance_is_related_with_last_month = models.CharField(max_length=100, null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    class Meta:
        db_table = 'AnalysisData'

    def __str__(self):
        return f'{self.analysis} - {self.wireless_number} - {self.data_type}'
    
    def save(self, *args, **kwargs):
        if self.bill_date:
            self.bill_date = parse_bill_date(self.bill_date)
            self.bill_day = self.bill_date.day
            self.bill_month = self.bill_date.month
            self.bill_year = self.bill_date.year
        super().save(*args, **kwargs)
    
    

    
class APIKey(models.Model):

    key = models.CharField(max_length=255, null=False)
    class Meta:
        db_table = 'APIKey'
    