from django.db import models
from Dashboard.ModelsByPage.DashAdmin import Vendors, EntryType, BanStatus, BanType, InvoiceMethod, PaymentType, CostCenterLevel, CostCenterType, BillType
from django.utils.timezone import now
from ..Organization.models import Organizations
from ..Company.models import Company
from..Location.models import Location
from authenticate.models import PortalUser
# Create your models here.
import datetime


# Base Account Number

class UploadBAN(models.Model):
    user_email = models.ForeignKey(PortalUser, null=True, blank=True, on_delete=models.CASCADE)
    Vendor_sub_id = models.CharField(max_length=255, null=True, blank=True)
    Vendor = models.ForeignKey(
        Vendors, null=True, related_name='vendors', on_delete=models.SET_NULL
    )
    company = models.ForeignKey(
        Company, related_name='companyBAN', on_delete=models.CASCADE, default=None
    )
    organization = models.ForeignKey(
        Organizations, related_name='bans', on_delete=models.CASCADE
    )

    entryType = models.ForeignKey(
        EntryType, related_name='entrytype', on_delete=models.SET_NULL, null=True
    )
    masteraccount = models.CharField(max_length=255, null=True, blank=True)

    is_it_consolidatedBan = models.BooleanField(default=False)
    location = models.ForeignKey(Location, related_name='location', on_delete=models.SET_NULL, null=True)
    banstatus = models.ForeignKey(
        BanStatus, related_name='banstatus', on_delete=models.SET_NULL, null=True, blank=True
    )

    auto_pay_enabled = models.BooleanField(default=False)
    vendor_alias = models.CharField(max_length=255, null=True, blank=True)
    vendorCS = models.CharField(max_length=255, null=True, blank=True)
    BillingCurrency = models.CharField(max_length=255, null=True, blank=True)

    ##########

    bantype = models.ForeignKey(
        BanType, related_name='bantype', on_delete=models.SET_NULL, null=True
    )
    invoicemethod = models.ForeignKey(
        InvoiceMethod, related_name='invoicemethod', on_delete=models.SET_NULL, null=True
    )
    paymenttype = models.ForeignKey(
        PaymentType, related_name='paytype', on_delete=models.SET_NULL, null=True
    )

    account_number = models.CharField(max_length=255, null=False, blank=False, unique=True)
    account_password = models.CharField(max_length=255, null=True, blank=True)
    payor = models.CharField(max_length=255, null=True, blank=True)
    GlCode = models.CharField(max_length=255, null=True, blank=True)
    ContractTerms = models.CharField(max_length=255, null=True, blank=True)
    ContractNumber = models.CharField(max_length=255, null=True, blank=True)
    Services = models.CharField(max_length=255, null=True, blank=True)
    Billing_cycle = models.CharField(max_length=255, null=True, blank=True)
    BillingDay = models.CharField(max_length=255, null=True, blank=True)
    PayTerm = models.CharField(max_length=255, null=True, blank=True)
    AccCharge = models.CharField(max_length=255, null=True, blank=True)
    CustomerOfRecord = models.CharField(max_length=255, null=True, blank=True)

    ### Cost Centers

    costcenterlevel = models.ForeignKey(
        CostCenterLevel, related_name='costcenterlevel', on_delete=models.SET_NULL, null=True, blank=True
    )
    costcentertype = models.ForeignKey(
        CostCenterType, related_name='costcentertype', on_delete=models.SET_NULL, null=True, blank=True
    )
    costcenterstatus = models.BooleanField(default=False)
    CostCenter = models.CharField(max_length=255, null=True, blank=True)
    CostCenterNotes = models.TextField(null=True, blank=True)
    PO = models.CharField(max_length=255, null=True, blank=True)
    Displaynotesonbillprocessing = models.BooleanField(default=False)
    POamt = models.CharField(max_length=255, null=True, blank=True)
    FoundAcc = models.CharField(max_length=255, null=True, blank=True)

    ### Billing Information

    BillingName = models.CharField(max_length=255, null=True, blank=True)
    BillingAdd = models.CharField(max_length=255, null=True, blank=True)
    BillingState = models.CharField(max_length=255, null=True, blank=True)
    BillingZip = models.CharField(max_length=255, null=True, blank=True)
    BillingCity = models.CharField(max_length=255, null=True, blank=True)
    BillingCountry = models.CharField(max_length=255, null=True, blank=True)
    BillingAtn = models.CharField(max_length=255, null=True, blank=True)
    BillingDate = models.CharField(max_length=255, null=True, blank=True)

    ### Remittance Information
    RemittanceName = models.CharField(max_length=255, null=True, blank=True)
    RemittanceAdd = models.CharField(max_length=255, null=False, blank=False)
    RemittanceState = models.CharField(max_length=255, null=False, blank=False)
    RemittanceZip = models.CharField(max_length=255, null=False, blank=False)
    RemittanceCity = models.CharField(max_length=255, null=False, blank=False)
    RemittanceCountry = models.CharField(max_length=255, null=True, blank=True)
    RemittanceAtn = models.CharField(max_length=255, null=True, blank=True)
    
    RemittanceNotes = models.CharField(max_length=255, null=True, blank=True)

    remarks = models.CharField(max_length=2550, null=True, blank=True)
    contract_name = models.CharField(max_length=2550, null=True, blank=True)
    contract_file = models.FileField(upload_to='ban-contracts/', null=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True, null=True)

    current_annual_review = models.CharField(max_length=2550, null=True, blank=True)
    previous_annual_review = models.CharField(max_length=2550, null=True, blank=True)
    variance = models.FloatField(default=5)

    class Meta:
        db_table = 'UploadBAN'
        constraints = [
            models.UniqueConstraint(fields=['company', 'organization', 'account_number'], name='unique_ban')
        ]

    def __str__(self):
        return self.account_number
    
class Lines(models.Model):
    account_number = models.ForeignKey(UploadBAN, on_delete=models.CASCADE, null=False, related_name="lines")
    wireless_number = models.CharField(max_length=255, null=False)
    username = models.CharField(max_length=255, null=False)
    planType = models.CharField(max_length=255, null=False)
    location = models.CharField(max_length=255, null=False)
    vendor_number = models.CharField(max_length=255, null=False)
    deviceid = models.CharField(max_length=255, null=True, blank=True)
    mobiledevice = models.CharField(max_length=255, null=True, blank=True)
    mobileIMEI = models.CharField(max_length=255, null=True, blank=True)
    mobileSIMnumber = models.CharField(max_length=255, null=True, blank=True)
    upgradeEligibleDate = models.CharField(max_length=255, null=True, blank=True)
    site_name = models.CharField(max_length=255, null=True, blank=True)
    voiceplanMins = models.CharField(max_length=255, null=True, blank=True)
    voiceplanCharges = models.CharField(max_length=255, null=True, blank=True)
    dataplanAllotment = models.CharField(max_length=255, null=True, blank=True)
    dataplanCharges = models.CharField(max_length=255, null=True, blank=True)
    mobileaccessCharges = models.CharField(max_length=255, null=True, blank=True)
    thirdpartyappCharge = models.CharField(max_length=255, null=True, blank=True)
    internationalvoiceFeat = models.CharField(max_length=255, null=True, blank=True)
    internationaldataFeat = models.CharField(max_length=255, null=True, blank=True)
    internationaltextFeat = models.CharField(max_length=255, null=True, blank=True)
    insurance = models.CharField(max_length=255, null=True, blank=True)
    userstatus = models.CharField(max_length=255, null=True, blank=True)
    useremail = models.CharField(max_length=255, null=True, blank=True)
    devicetype = models.CharField(max_length=255, null=True, blank=True)
    devicesmake = models.CharField(max_length=255, null=True, blank=True)
    devicesmodel = models.CharField(max_length=255, null=True, blank=True)
    devicescolor = models.CharField(max_length=255, null=True, blank=True)
    devicesstorage = models.CharField(max_length=255, null=True, blank=True)
    devicesOS = models.CharField(max_length=255, null=True, blank=True)
    deviceSerialnumber = models.CharField(max_length=255, null=True, blank=True)
    deviceETF = models.CharField(max_length=255, null=True, blank=True)
    deviceAmount = models.CharField(max_length=255, null=True, blank=True)
    deviceCredit = models.CharField(max_length=255, null=True, blank=True)
    planName = models.CharField(max_length=255, null=True, blank=True)
    planlineNumber = models.CharField(max_length=255, null=True, blank=True)
    location_address_1 = models.CharField(max_length=255, null=True, blank=True)
    location_address_2 = models.CharField(max_length=255, null=True, blank=True)
    location_city = models.CharField(max_length=255, null=True, blank=True)
    location_state = models.CharField(max_length=255, null=True, blank=True)
    location_zip = models.CharField(max_length=255, null=True, blank=True)
    cost_center = models.CharField(max_length=255, null=True, blank=True)
    cost_center_status = models.CharField(max_length=255, null=True, blank=True)
    cost_center_notes = models.CharField(max_length=255, null=True, blank=True)

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True, null=True)

    class Meta:
        db_table = 'Lines'
        unique_together = (('account_number', 'wireless_number'),)

    def __str__(self):
        return f'{self.wireless_number}-{self.username}'
    

    
class OnboardBan(models.Model):
    organization = models.ForeignKey(
        Organizations, related_name='onboardban_organization', on_delete=models.CASCADE, null=True
    )
    vendor = models.ForeignKey(
        Vendors, null=True, related_name='onboardban_vendors', on_delete=models.SET_NULL
    )
    entryType = models.ForeignKey(
        EntryType, related_name='entrytypeban', on_delete=models.SET_NULL, null=True
    )
    masteraccount = models.ForeignKey(
        UploadBAN, related_name='masteraccOnboardBan', on_delete=models.SET_NULL, null=True)
    is_it_consolidatedBan = models.BooleanField(default=False)
    account_number = models.CharField(max_length=100, null=True, blank=True)
    location = models.ForeignKey(Location, related_name='locationOnboardBan', on_delete=models.SET_NULL, null=True)

    addDataToBaseline = models.BooleanField(default=False)
    uploadBill = models.FileField(upload_to='BanUploadBill/')
    billType = models.ForeignKey(BillType, related_name='billtypes', on_delete=models.SET_NULL, null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True, null=True)
    variance = models.FloatField(default=5)
    is_processed = models.BooleanField(default=False) 
    
    class Meta:
        db_table = 'OnboardBAN'

    def __str__(self):
        return f'{self.organization.Organization_name} - {self.vendor.name} - {self.uploadBill.name}'


class InventoryUpload(models.Model):
    organization = models.ForeignKey(
        Organizations, related_name='inventoryupload_organizations', on_delete=models.CASCADE
    )
    vendor = models.ForeignKey(
        Vendors, null=True, related_name='inventoryupload_vendors', on_delete=models.SET_NULL
    )
    ban = models.CharField(max_length=255, null=True, blank=True)
    uploadFile = models.FileField(upload_to='InventoryExcel/')
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True, null=True)

    class Meta:
        db_table = 'InventoryUpload'
    def __str__(self):
        return f'{self.organization.Organization_name} - {self.ban} - {self.uploadFile.name}'
    
from View.models import ViewUploadBill
class MappingObjectBan(models.Model):
    onboard = models.ForeignKey(OnboardBan, related_name='onboard', on_delete=models.CASCADE,null=True, blank=True )
    inventory = models.ForeignKey(InventoryUpload, related_name='inventory', on_delete=models.CASCADE, null=True, blank=True)
    ban = models.ForeignKey(UploadBAN, related_name='ban', on_delete=models.CASCADE, null=True, blank=True)
    viewupload = models.ForeignKey(ViewUploadBill, related_name='viewupload', on_delete=models.CASCADE, null=True, blank=True)
    bill_date =  models.CharField(max_length=255, null=False, blank=True)
    invoice_number =  models.CharField(max_length=255, null=True, blank=True)
    account_number = models.CharField(max_length=255, null=False, blank=True)
    vendor = models.CharField(max_length=255, null=False, blank=True)
    wireless_number = models.CharField(max_length=255, null=False, blank=True)
    user_name = models.CharField(max_length=255, null=True, blank=True)
    site_name = models.CharField(max_length=255, null=True, blank=True)
    mobile_device = models.CharField(max_length=255, null=True, blank=True)

    imei_number = models.CharField(max_length=255, null=True, blank=True)
    mobile_sim_num = models.CharField(max_length=255, null=True, blank=True)
    upgrade_eligible_date = models.CharField(max_length=255, null=True, blank=True)
    voice_plan_mins = models.CharField(max_length=255, null=True, blank=True)
    voice_plan_charges = models.CharField(max_length=255, null=True, blank=True)
    data_plan_allotment = models.CharField(max_length=255, null=True, blank=True)
    data_plan_charges = models.CharField(max_length=255, null=True, blank=True)
    mobile_access_charge = models.CharField(max_length=255, null=True, blank=True)
    third_party_app_charge = models.CharField(max_length=255, null=True, blank=True)
    international_voice_feat = models.CharField(max_length=255, null=True, blank=True)
    international_data_feat = models.CharField(max_length=255, null=True, blank=True)
    international_text_feat = models.CharField(max_length=255, null=True, blank=True)
    insurance = models.CharField(max_length=255, null=True, blank=True)
    device_id = models.CharField(max_length=255, null=True, blank=True)
    VendorNumber = models.CharField(max_length=255, null=True,blank=True)
    cost_centers = models.CharField(max_length=255, null=True,blank=True)
    User_status = models.CharField(max_length=255, null=True, blank=True)
    User_email = models.CharField(max_length=255, null=True, blank=True)
    Devices_device_type = models.CharField(max_length=255, null=True, blank=True)
    Devices_make = models.CharField(max_length=255, null=True, blank=True)
    Devices_model = models.CharField(max_length=255, null=True, blank=True)
    Devices_color = models.CharField(max_length=255, null=True, blank=True)
    Devices_storage = models.CharField(max_length=255, null=True, blank=True)
    Devices_os = models.CharField(max_length=255, null=True, blank=True)
    Devices_serial_number = models.CharField(max_length=255, null=True, blank=True)
    Device_ETF = models.CharField(max_length=255, null=True, blank=True)
    DeviceAmount = models.CharField(max_length=255, null=True, blank=True)
    DeviceCredit = models.CharField(max_length=255, null=True, blank=True)
    Plan_name = models.CharField(max_length=255, null=True, blank=True)
    plan_type = models.CharField(max_length=255, null=True, blank=True)
    Plan_line_number = models.CharField(max_length=255, null=True, blank=True)
    Location_address_1 = models.CharField(max_length=255, null=True, blank=True)
    Location_address_2 = models.CharField(max_length=255, null=True, blank=True)
    Location_city = models.CharField(max_length=255, null=True, blank=True)
    Location_state = models.CharField(max_length=255, null=True, blank=True)
    Location_zip = models.CharField(max_length=255, null=True, blank=True)
    
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True, null=True)

    class Meta:
        db_table = 'MappingObjectBan'

    def __str__(self):
        return f'{self.account_number}'

class PdfDataTable(models.Model):
    banOnboarded = models.ForeignKey(OnboardBan, related_name='banOnboardedpdf', on_delete=models.CASCADE, null=True, blank=True)
    viewuploaded = models.ForeignKey(ViewUploadBill, related_name='viewpdf', on_delete=models.CASCADE, null=True, blank=True)
    company = models.CharField(max_length=255, blank=True, null=True, default="")
    account_number = models.CharField(max_length=255, blank=True, null=True, default="")
    wireless_number = models.CharField(max_length=255, blank=True, null=True, default="")
    user_name = models.CharField(max_length=255, blank=True, null=True, default="")
    plans = models.CharField(max_length=255, blank=True, null=True, default="")
    cost_center = models.CharField(max_length=255, blank=True, null=True, default="")
    account_charges_and_credits = models.CharField(max_length=255, blank=True, null=True, default="")
    monthly_charges = models.CharField(max_length=255, blank=True, null=True, default="")
    usage_and_purchase_charges = models.CharField(max_length=255, blank=True, null=True, default="")
    equipment_charges = models.CharField(max_length=255, blank=True, null=True, default="")
    surcharges_and_other_charges_and_credits = models.CharField(max_length=255, blank=True, null=True, default="")
    taxes_governmental_surcharges_and_fees = models.CharField(max_length=255, blank=True, null=True, default="")
    third_party_charges_includes_tax = models.CharField(max_length=255, blank=True, null=True, default="")
    total_charges = models.CharField(max_length=255, blank=True, null=True, default="")
    voice_plan_usage = models.CharField(max_length=255, blank=True, null=True, default="")
    data_usage = models.CharField(max_length=255, blank=True, null=True, default="")
    group_number = models.CharField(max_length=255, blank=True, null=True, default="")
    messaging_usage = models.CharField(max_length=255, blank=True, null=True, default="")
    user_email = models.CharField(max_length=255, blank=True, null=True, default="")
    status = models.CharField(max_length=255, blank=True, null=True, default="")
    cost_center = models.CharField(max_length=255, blank=True, null=True, default="")
    account_charges_credits = models.CharField(max_length=255, blank=True, null=True, default="")
    charges = models.CharField(max_length=255, blank=True, null=True, default="")
    sub_company = models.CharField(max_length=255, blank=True, null=True, default="")
    location = models.CharField(max_length=255, blank=True, null=True, default="")
    item_category =  models.CharField(max_length=255, blank=True, null=True, default="")
    item_description =  models.CharField(max_length=255, blank=True, null=True, default="")
    item_charges = models.CharField(max_length=255, blank=True, null=True, default="")
    
    
    vendor = models.CharField(max_length=255, blank=True, null=True, default="")
    
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True, null=True)

    class Meta:
        db_table = 'PdfDataTable'
    def __str__(self):
        return self.account_number
    
from View.models import ViewUploadBill,PaperBill
class BaseDataTable(models.Model):
    banUploaded = models.ForeignKey(UploadBAN, related_name='banUploadedBase', on_delete=models.CASCADE, null=True, blank=True)
    banOnboarded = models.ForeignKey(OnboardBan, related_name='banOnboardedBase', on_delete=models.CASCADE, null=True, blank=True)
    viewuploaded = models.ForeignKey(ViewUploadBill, related_name='viewbase', on_delete=models.CASCADE, null=True, blank=True)
    viewpapered = models.ForeignKey(PaperBill, related_name='paperbase', on_delete=models.CASCADE, null=True, blank=True)
    inventory = models.ForeignKey(InventoryUpload, related_name='inventorybase', on_delete=models.CASCADE, null=True, blank=True)
    bill_date = models.CharField(max_length=255, blank=True, null=True, default="")
    date_due = models.CharField(max_length=255, blank=True, null=True, default="")
    accountnumber = models.CharField(max_length=255, blank=True, null=True, default="")
    auto_pay_enabled = models.BooleanField(default=False, null=True)
    invoicenumber = models.CharField(max_length=255, blank=True, null=True, default="")
    duration = models.CharField(max_length=255, blank=True, null=True, default="")
    total_charges = models.CharField(max_length=255, blank=True, null=True, default="")
    company = models.CharField(max_length=255, blank=True, null=True, default="")
    Entry_type = models.CharField(max_length=255, blank=True, null=True, default="")
    vendor = models.CharField(max_length=255, blank=True, null=True, default="")
    sub_company = models.CharField(max_length=255, blank=True, null=True, default="")
    location = models.CharField(max_length=255, blank=True, null=True, default="")
    master_account = models.CharField(max_length=255, blank=True, null=True, default="")
    website = models.CharField(max_length=255, blank=True, null=True, default="")
    Total_Current_Charges = models.CharField(max_length=255, blank=True, null=True, default="")
    
    plans = models.CharField(max_length=255, blank=True, null=True, default="")
    
    charges = models.CharField(max_length=255, blank=True, null=True, default="")
    location = models.CharField(max_length=255, blank=True, null=True, default="")
    RemittanceAdd = models.CharField(max_length=255, blank=True, null=True, default="")

    BillingName = models.CharField(max_length=255, blank=True, null=True, default="")
    BillingAdd = models.CharField(max_length=255, blank=True, null=True, default="")

    Total_Amount_Due =  models.CharField(max_length=255, blank=True, null=True, default="")

    current_annual_review = models.CharField(max_length=2550, null=True, blank=True)
    previous_annual_review = models.CharField(max_length=2550, null=True, blank=True)

     ### Billing Information

    BillingState = models.CharField(max_length=255, null=True, blank=True, default="")
    BillingZip = models.CharField(max_length=255, null=True, blank=True, default="")
    BillingCity = models.CharField(max_length=255, null=True, blank=True, default="")
    BillingCountry = models.CharField(max_length=255, null=True, blank=True, default="United States")
    BillingAtn = models.CharField(max_length=255, null=True, blank=True, default="")
    BillingDate = models.CharField(max_length=255, null=True, blank=True, default="")
    is_production = models.BooleanField(default=False)
    ### Remittance Information
    RemittanceName = models.CharField(max_length=255, null=True, blank=True, default="")
    RemittanceState = models.CharField(max_length=255, null=False, blank=False, default="")
    RemittanceZip = models.CharField(max_length=255, null=False, blank=False, default="")
    RemittanceCity = models.CharField(max_length=255, null=False, blank=False, default="")
    RemittanceCountry = models.CharField(max_length=255, null=True, blank=True, default="United States")
    RemittanceAtn = models.CharField(max_length=255, null=True, blank=True, default="")
    RemittanceNotes = models.CharField(max_length=255, null=True, blank=True, default="")

    costcenterlevel = models.CharField(max_length=255, null=True, blank=True, default="")
    costcentertype = models.CharField(max_length=255, null=True, blank=True, default="")

    costcenterstatus = models.BooleanField(default=False)
    CostCenter = models.CharField(max_length=255, null=True, blank=True)
    CostCenterNotes = models.TextField(null=True, blank=True)
    PO = models.CharField(max_length=255, null=True, blank=True)
    Displaynotesonbillprocessing = models.BooleanField(default=False)
    POamt = models.CharField(max_length=255, null=True, blank=True)
    FoundAcc = models.CharField(max_length=255, null=True, blank=True)
    bantype = models.CharField(max_length=255, null=True, blank=True, default="")
    invoicemethod =models.CharField(max_length=255, null=True, blank=True, default="")

    vendorCS = models.CharField(max_length=255, null=True, blank=True)
    
    vendor_alias = models.CharField(max_length=255, null=True, blank=True)

    month =  models.CharField(max_length=255, blank=True, null=True, default="")
    year =  models.CharField(max_length=255, blank=True, null=True, default="")
    pdf_filename = models.CharField(max_length=255, blank=True, null=True, default="")
    pdf_path = models.CharField(max_length=255, blank=True, null=True, default="")
    remarks = models.CharField(max_length=2550, null=True, blank=True)

    account_password = models.CharField(max_length=255, null=True, blank=True)
    vendor_id = models.CharField(max_length=255, null=True, blank=True)
    payor = models.CharField(max_length=255, null=True, blank=True)
    GlCode = models.CharField(max_length=255, null=True, blank=True)
    ContractTerms = models.CharField(max_length=255, null=True, blank=True)
    ContractNumber = models.CharField(max_length=255, null=True, blank=True)
    Services = models.CharField(max_length=255, null=True, blank=True)
    Billing_cycle = models.CharField(max_length=255, null=True, blank=True)
    BillingDay = models.CharField(max_length=255, null=True, blank=True)
    PayTerm = models.CharField(max_length=255, null=True, blank=True)
    AccCharge = models.CharField(max_length=255, null=True, blank=True)
    CustomerOfRecord = models.CharField(max_length=255, null=True, blank=True)

    contract_name = models.CharField(max_length=255, null=True, blank=True)
    contract_file = models.FileField(upload_to='ban-contracts/', null=True)

    paymentType = models.CharField(max_length=255, null=True, blank=True, default="")
    billstatus = models.CharField(max_length=255, null=True, blank=True, default="Active")
    banstatus = models.CharField(max_length=255, null=True, blank=True,default="Active")
    Check = models.CharField(max_length=255, null=True, blank=True)
    summary_file = models.FileField(upload_to='view_summary_files/', null=True, blank=True)
    is_baseline_approved = models.BooleanField(default=False)
    batch_approved = models.CharField(max_length=255, null=True, blank=True, default='Pending')
    batch_approved_changer = models.CharField(max_length=255, null=True, blank=True, default='')
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True, null=True)

    workbook_path = models.CharField(max_length=255, null=True, blank=True)

    baseline_notes = models.TextField(null=True, blank=True)
    
    net_amount = models.CharField(max_length=255, blank=True, null=True, default=0)

    batch_file = models.FileField(upload_to='batchfiles/', null=True, blank=True, default=None)
    variance = models.FloatField(default=5)

    def save(self, *args, **kwargs):
        
        if self.viewuploaded or self.viewpapered:
            self.variance = 0
        super().save(*args, **kwargs)

    class Meta:
        db_table = 'BaseDataTable'
    def __str__(self):
        return self.accountnumber
    
class UniquePdfDataTable(models.Model):
    banOnboarded = models.ForeignKey(OnboardBan, related_name='onboardedlines', on_delete=models.CASCADE, null=True, blank=True)
    banUploaded = models.ForeignKey(UploadBAN, related_name='uploadedlines', on_delete=models.CASCADE, null=True, blank=True)
    inventory = models.ForeignKey(InventoryUpload, related_name='inventorylines', on_delete=models.CASCADE, null=True, blank=True)
    viewuploaded = models.ForeignKey(ViewUploadBill, related_name='viewunique', on_delete=models.CASCADE, null=True, blank=True)
    viewpapered = models.ForeignKey(PaperBill, related_name='paperunique', on_delete=models.CASCADE, null=True, blank=True)
    account_number = models.CharField(max_length=255, blank=True, null=True, default="")
    ECPD_Profile_ID = models.CharField(max_length=255, blank=True, null=True, default="")
    wireless_number = models.CharField(max_length=255, blank=True, null=True, default="")
    user_name = models.CharField(max_length=255, blank=True, null=True, default="")
    plans = models.CharField(max_length=255, blank=True, null=True, default="")

    #plans attributes

    plan_type = models.CharField(max_length=255, blank=True, null=True)
    data_allotment = models.CharField(max_length=255, null=True, blank=True)
    plan_fee = models.FloatField(default=0)
    smartphone = models.FloatField(default=0)
    tablet_computer = models.FloatField(default=0)
    mifi = models.FloatField(default=0)
    wearables = models.FloatField(default=0)

    cost_center = models.CharField(max_length=255, blank=True, null=True, default="")
    VendorNumber = models.CharField(max_length=255, null=True,blank=True)
    bill_date = models.CharField(max_length=255, blank=True, null=True, default="")
    account_charges_and_credits = models.CharField(max_length=255, blank=True, null=True, default="")
    monthly_charges = models.CharField(max_length=255, blank=True, null=True, default="")
    usage_and_purchase_charges = models.CharField(max_length=255, blank=True, null=True, default="")
    equipment_charges = models.CharField(max_length=255, blank=True, null=True, default="")
    surcharges_and_other_charges_credits = models.CharField(max_length=255, blank=True, null=True, default="")
    taxes_governmental_surcharges_and_fees = models.CharField(max_length=255, blank=True, null=True, default="")
    third_party_charges_includes_tax = models.CharField(max_length=255, blank=True, null=True, default="")
    total_charges = models.CharField(max_length=255, blank=True, null=True, default="")
    voice_plan_usage = models.CharField(max_length=255, blank=True, null=True, default="")
    messaging_usage = models.CharField(max_length=255, blank=True, null=True, default="")
    data_usage = models.CharField(max_length=255, blank=True, null=True, default="")
    group_number = models.CharField(max_length=255, blank=True, null=True, default="")
    sub_company = models.CharField(max_length=255, blank=True, null=True, default="")
    company = models.CharField(max_length=255, blank=True, null=True, default="")
    vendor = models.CharField(max_length=255, blank=True, null=True, default="")
    entry_type = models.CharField(max_length=255, blank=True, null=True, default="")
    mobile_device = models.CharField(max_length=255, blank=True, null=True, default="")
    imei_number = models.CharField(max_length=255, blank=True, null=True, default="")
    mobile_sim_num = models.CharField(max_length=255, blank=True, null=True, default="")
    User_status = models.CharField(max_length=255, blank=True, null=True, default="Active")
    User_email = models.CharField(max_length=255, blank=True, null=True, default="")
    Devices_device_type = models.CharField(max_length=255, blank=True, null=True, default="")
    Devices_make = models.CharField(max_length=255, blank=True, null=True, default="")
    Devices_model = models.CharField(max_length=255, blank=True, null=True, default="")
    Devices_color = models.CharField(max_length=255, blank=True, null=True, default="")
    Devices_storage = models.CharField(max_length=255, blank=True, null=True, default="")
    Devices_os = models.CharField(max_length=255, blank=True, null=True, default="")
    Devices_serial_number = models.CharField(max_length=255, blank=True, null=True, default="")
    Device_ETF = models.CharField(max_length=255, blank=True, null=True, default="")
    Plan_name = models.CharField(max_length=255, blank=True, null=True, default="")
    Plan_line_number = models.CharField(max_length=255, blank=True, null=True, default="")
    Location_address_1 = models.CharField(max_length=255, blank=True, null=True, default="")
    Location_address_2 = models.CharField(max_length=255, blank=True, null=True, default="")
    Location_city = models.CharField(max_length=255, blank=True, null=True, default="")
    Location_state = models.CharField(max_length=255, blank=True, null=True, default="")
    Location_zip = models.CharField(max_length=255, blank=True, null=True, default="")
    site_name = models.CharField(max_length=255, blank=True, null=True, default="")
    upgrade_eligible_date = models.CharField(max_length=255, blank=True, null=True, default="")
    voice_plan_mins = models.CharField(max_length=255, blank=True, null=True, default="")
    voice_plan_charges = models.CharField(max_length=255, blank=True, null=True, default="")
    data_plan_allotment = models.CharField(max_length=255, blank=True, null=True, default="")
    data_plan_charges = models.CharField(max_length=255, blank=True, null=True, default="")
    mobile_access_charge = models.CharField(max_length=255, blank=True, null=True, default="")
    third_party_app_charge = models.CharField(max_length=255, blank=True, null=True, default="")
    international_voice_feat = models.CharField(max_length=255, blank=True, null=True, default="")
    international_data_feat = models.CharField(max_length=255, blank=True, null=True, default="")
    international_text_feat = models.CharField(max_length=255, blank=True, null=True, default="")
    insurance = models.CharField(max_length=255, blank=True, null=True, default="")
    device_id = models.CharField(max_length=255, blank=True, null=True, default="")
    cost_centers = models.CharField(max_length=255, blank=True, null=True, default="")
    deviceAmount = models.CharField(max_length=255, null=True, blank=True)
    deviceCredit = models.CharField(max_length=255, null=True, blank=True)
    cost_center = models.CharField(max_length=255, null=True, blank=True)
    cost_center_status = models.CharField(max_length=255, null=True, blank=True)
    cost_center_notes = models.CharField(max_length=255, null=True, blank=True)
    item_category =  models.CharField(max_length=255, blank=True, null=True, default="")
    item_description =  models.CharField(max_length=255, blank=True, null=True, default="")
    category_object = models.JSONField(default=dict, null=True, blank=True)

    remark = models.CharField(max_length=255, blank=True, null=True)

    is_baseline_approved = models.BooleanField(default=False)
    
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True, null=True)
    
    class Meta:
        
        db_table = 'UniquePdfDataTable'

    # def __str__(self):
    #     return self.account_number if self.account_number else None

class BaselineDataTable(models.Model):
    banUploaded = models.ForeignKey(UploadBAN, related_name='banUploadedbaseline', on_delete=models.CASCADE, null=True, blank=True)
    banOnboarded = models.ForeignKey(OnboardBan, related_name='banOnboardedbaseline', on_delete=models.CASCADE, null=True, blank=True)
    viewuploaded = models.ForeignKey(ViewUploadBill, related_name='viewbaseline', on_delete=models.CASCADE, null=True, blank=True)
    viewpapered = models.ForeignKey(PaperBill, related_name='paperbaseline', on_delete=models.CASCADE, null=True, blank=True)
    account_number = models.CharField(max_length=255, blank=True, null=True, default="")
    Wireless_number = models.CharField(max_length=255, blank=True, null=True, default="")
    user_name = models.CharField(max_length=255, blank=True, null=True, default="")
    plans = models.CharField(max_length=255, blank=True, null=True, default="")

    #plans attributes

    plan_type = models.CharField(max_length=255, blank=True, null=True)
    data_allotment = models.CharField(max_length=255, null=True, blank=True)
    plan_fee = models.FloatField(default=0)
    smartphone = models.FloatField(default=0)
    tablet_computer = models.FloatField(default=0)
    mifi = models.FloatField(default=0)
    wearables = models.FloatField(default=0)

    cost_center = models.CharField(max_length=255, blank=True, null=True, default="")
    account_charges_and_credits = models.CharField(max_length=255, blank=True, null=True, default="")
    monthly_charges = models.CharField(max_length=255, blank=True, null=True, default="")
    usage_and_purchase_charges = models.CharField(max_length=255, blank=True, null=True, default="")
    equipment_charges = models.CharField(max_length=255, blank=True, null=True, default="")
    data_usage = models.CharField(max_length=255, blank=True, null=True, default="")
    surcharges_and_other_charges_and_credits = models.CharField(max_length=255, blank=True, null=True, default="")
    taxes_governmental_surcharges_and_fees = models.CharField(max_length=255, blank=True, null=True, default="")
    third_party_charges_includes_tax = models.CharField(max_length=255, blank=True, null=True, default="")
    total_charges = models.CharField(max_length=255, blank=True, null=True, default="")
    voice_plan_usage = models.CharField(max_length=255, blank=True, null=True, default="")
    VendorNumber = models.CharField(max_length=255, null=True,blank=True)
    messaging_usage = models.CharField(max_length=255, blank=True, null=True, default="")
    sub_company = models.CharField(max_length=255, blank=True, null=True, default="")
    category_object = models.JSONField(default=dict)
    company = models.CharField(max_length=255, blank=True, null=True, default="")
    vendor = models.CharField(max_length=255, blank=True, null=True, default="")
    bill_date = models.CharField(max_length=255, blank=True, null=True, default="")
    remark =  models.CharField(max_length=255, blank=True, null=True)
    is_baseline_approved = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True, null=True)
    is_pending = models.BooleanField(default=False)
    is_draft = models.BooleanField(default=False)

    paymentstatus = models.CharField(max_length=255, null=True, blank=True, default="Pending")
    class Meta:
        db_table = 'BaselineDataTable'

    def __str__(self):
        return self.account_number
    
class BatchReport(models.Model):
    banUploaded = models.ForeignKey(UploadBAN, related_name='banUploadedbatch', on_delete=models.CASCADE, null=True, blank=True)
    banOnboarded = models.ForeignKey(OnboardBan, related_name='banOnboardedbatchreport', on_delete=models.CASCADE, null=True, blank=True)
    viewuploaded = models.ForeignKey(ViewUploadBill, related_name='viewbatch', on_delete=models.CASCADE, null=True, blank=True)
    viewpapered = models.ForeignKey(PaperBill, related_name='paperbatch', on_delete=models.CASCADE, null=True, blank=True)
    Cust_Id = models.CharField(max_length=100, null=True, blank=True, default="")
    Sub_Id = models.CharField(max_length=100, null=True, blank=True, default="")
    Vendor_Number = models.CharField(max_length=100, null=True, blank=True, default="")
    Location_Code = models.CharField(max_length=100, null=True, blank=True, default="")
    Payment_Comments = models.CharField(max_length=255, null=True, blank=True, default="")
    Payment_Number = models.CharField(max_length=100, null=True, blank=True, default="")
    Vendor_Name_1 = models.CharField(max_length=255, null=True, blank=True, default="")
    Vendor_Name_2 = models.CharField(max_length=255, null=True, blank=True, default="")
    Vendor_Address_1 = models.CharField(max_length=255, null=True, blank=True, default="")
    Vendor_Address_2 = models.CharField(max_length=255, null=True, blank=True, default="")
    Vendor_City = models.CharField(max_length=100, null=True, blank=True, default="")
    Vendor_State = models.CharField(max_length=100, null=True, blank=True, default="")
    Vendor_Zip = models.CharField(max_length=100, null=True, blank=True, default="")
    Vendor_Country = models.CharField(max_length=100, null=True, blank=True, default="")
    Vendor_Tax_Id = models.CharField(max_length=100, null=True, blank=True, default="")
    Vendor_Phone_Number = models.CharField(max_length=100, null=True, blank=True, default="")
    Customer_Vendor_Account_Number = models.CharField(max_length=100, null=True, blank=True, default="")
    Payment_Misc_1 = models.CharField(max_length=255, null=True, blank=True, default="") 
    Invoice_Number = models.CharField(max_length=100, null=True, blank=True, default="")
    Total_Amount = models.CharField(max_length=100, null=True, blank=True, default="")
    Adjustment_Amount = models.CharField(max_length=100, null=True, blank=True, default="")
    Net_Amount = models.CharField(max_length=100, null=True, blank=True, default="")
    Due_Date = models.CharField(max_length=100, null=True, blank=True, default="")
    Invoice_Date = models.CharField(max_length=100, null=True, blank=True, default="")
    Invoice_Comments = models.CharField(max_length=255, null=True, blank=True, default="")
    Invoice_Misc_1 = models.CharField(max_length=255, null=True, blank=True, default="")
    company = models.CharField(max_length=255, null=True, blank=True, default="")
    remmitance_country = models.CharField(max_length=255, null=True, blank=True, default="")
    month = models.CharField(max_length=100,null=True, default="")
    year = models.CharField(max_length=100,null=True, default="")
    email = models.CharField(max_length=100,null=True, default="")
    sub_company_name = models.CharField(max_length=100,null=True, default="")
    Total_Current_Charges = models.CharField(max_length=100,null=True, default="")
    duration = models.CharField(max_length=100,null=True, default="")
    sub_company = models.CharField(max_length=100,null=True, default="")
    billing_day = models.CharField(max_length=255, blank=True, null=True)
    is_downloaded = models.CharField(max_length=255, blank=True, null=True, default="False")
    approved = models.CharField(max_length=255, null=True, blank=True, default='Pending')
    approved_changer = models.CharField(max_length=255, null=True, blank=True, default='')
    Entry_type = models.CharField(max_length=255, blank=True, default=None, null=True)
    location = models.CharField(max_length=255, blank=True, default=None, null=True)
    master_account = models.CharField(max_length=255, blank=True, default=None, null=True)
    Total_Amount_Due = models.CharField(max_length=255, blank=True, default=None, null=True)

    output_file = models.FileField(upload_to='batchfiles/', null=True, blank=True, default=None)
    
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True, null=True)


    class Meta:
        db_table = 'BatchReport'

class PortalInformation(models.Model):
    banUploaded = models.ForeignKey(UploadBAN, related_name='uploadedportalinfo', on_delete=models.CASCADE, null=True, blank=True)
    banOnboarded = models.ForeignKey(OnboardBan, related_name='banOnboardedportalinfo', on_delete=models.CASCADE, null=True, blank=True)
    URL = models.CharField(max_length=1000, null=True, blank=True)
    Username = models.CharField(max_length=250, null=True, blank=True)
    Password = models.CharField(max_length=250, null=True, blank=True)
    Customer_Name = models.CharField(max_length=250, null=True, blank=True)
    Vendor = models.CharField(max_length=250, null=True, blank=True)
    Account_number = models.CharField(max_length=250, null=True, blank=True)
    User_email_id = models.CharField(max_length=250, null=True, blank=True)
    Automated = models.CharField(max_length=250, null=True, blank=True)
    On_Email = models.CharField(max_length=250, null=True, blank=True)
    
    class Meta:
        db_table = 'PortalInformation'
    
    