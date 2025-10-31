from django.db import models
from OnBoard.Company.models import Company
from OnBoard.Organization.models import Organizations
from Dashboard.ModelsByPage.DashAdmin import Vendors


class PaperBill(models.Model):
    sub_company = models.CharField(max_length=255, null=False)
    vendor = models.CharField(max_length=255, null=False)
    account_number = models.CharField(max_length=255, null=False)
    invoice_number = models.CharField(max_length=255, null=True, blank=True)
    bill_date = models.CharField(max_length=255, null=True, blank=True)
    due_date = models.CharField(max_length=255, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'PaperBill'
    
        constraints = [
            models.UniqueConstraint(fields=['sub_company', 'vendor','account_number','bill_date'], name='unique_paperbill')
        ]
    def __str__(self):
        return f'{self.invoice_number}'

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
    ban = models.CharField(max_length=255, null=True, blank=True)
    types = models.CharField(max_length=255, null=True, blank=True)



    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    output_file = models.FileField(upload_to='ViewUploadedBills/', null=True, blank=True)
    is_processed = models.BooleanField(default=False) 

    

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



from OnBoard.Ban.models import UploadBAN, OnboardBan

class Contracts(models.Model):
    onboardedban = models.ForeignKey(OnboardBan, related_name='onboarded_ban_contracts', on_delete=models.CASCADE, null=True, blank=True)
    uploadedban = models.ForeignKey(UploadBAN, related_name='uploaded_ban_contracts', on_delete=models.CASCADE, null=True, blank=True)
    sub_company = models.CharField(max_length=255, null=True, blank=True)
    person = models.CharField(max_length=255, null=True, blank=True)
    term = models.CharField(max_length=255, null=True, blank=True)
    status = models.CharField(max_length=255, null=True, blank=True,default="Active")
    notes = models.CharField(max_length=255, null=True, blank=True)
    contract_file = models.FileField(upload_to='ban-contracts/', null=True, blank=True)
    contract_name = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    class Meta:
        db_table = 'Contracts'
    
    def __str__(self):
        return f'Contract for {self.onboardedban.account_number if self.onboardedban else self.uploadedban.account_number}'
    

from dateutil import parser
from django.core.validators import RegexValidator

def parse_bill_date(date_str):
        try:
            return parser.parse(date_str, dayfirst=False)  # US-style month/day
        except Exception:
            raise ValueError(f"Date format not supported: {date_str}")
        

class BillSummaryData(models.Model):
    bill_id = models.ForeignKey(ViewUploadBill, on_delete=models.CASCADE, related_name="bill_summary_data")
    company = models.CharField(max_length=255, null=True, blank=True)
    vendor = models.CharField(max_length=255, null=True, blank=True)
    file_name = models.CharField(max_length=255, null=False)
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
        db_table = 'BillSummaryData'

    def save(self, *args, **kwargs):
        if self.bill_date:
            self.bill_date = parse_bill_date(self.bill_date)
            self.bill_day = self.bill_date.day
            self.bill_month = self.bill_date.month
            self.bill_year = self.bill_date.year
        super().save(*args, **kwargs)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['wireless_number', 'bill_date', 'bill_id'],
                name='bill_unique_wireless_number_bill_date_id'
            )
        ]

class BillAnalysisData(models.Model):
    bill_id = models.ForeignKey(ViewUploadBill, on_delete=models.CASCADE, related_name="bill_analysis_data")
    company = models.CharField(max_length=255, null=True, blank=True)
    vendor = models.CharField(max_length=255, null=True, blank=True)
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
        db_table = 'BillAnalysisData'

    def __str__(self):
        return f'{self.bill_id} - {self.wireless_number} - {self.data_usage_range}'
    
