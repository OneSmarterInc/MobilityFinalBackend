from django.db import models
from OnBoard.Organization.models import Organizations
from .DashAdmin import Vendors
from authenticate.models import PortalUser
from django.utils import timezone

class Requests(models.Model):
    organization = models.ForeignKey(Organizations, related_name="reuqest_organizations", null=False,on_delete=models.CASCADE)
    requester = models.ForeignKey(PortalUser, related_name="reuqest_users", null=False,on_delete=models.CASCADE)
    request_type = models.CharField(max_length=255, null=False)
    request_date = models.DateTimeField(default=timezone.now, null=True, blank=True)

    ban = models.CharField(max_length=255, null=False,default="")

    vendor = models.ForeignKey(Vendors, related_name="reuqest_vendors", null=False,on_delete=models.CASCADE)
    device_type = models.CharField(max_length=255, null=True, blank=True)
    device = models.CharField(max_length=255, null=True, blank=True)
    mobile = models.CharField(max_length=255, null=True, blank=True)
    user_name = models.CharField(max_length=255, null=True, blank=True)
    line_of_service = models.CharField(max_length=255, null=True, blank=True)
    forward_end_date = models.DateTimeField(null=True, blank=True)
    cancel_date = models.DateTimeField(null=True, blank=True)
    plan = models.CharField(max_length=255, null=True, blank=True)
    shipping_method = models.CharField(max_length=255, null=True, blank=True)
    model = models.CharField(max_length=255, null=True, blank=True)
    device_color = models.CharField(max_length=255, null=True, blank=True)
    device_storage = models.CharField(max_length=255, null=True, blank=True)
    request_tracking_id = models.CharField(max_length=255, null=True, blank=True)

    ## Accessories
    cases = models.CharField(max_length=255, null=True, blank=True)
    screen_protector = models.CharField(max_length=255, null=True, blank=True)
    features = models.JSONField(default=list, null=True, blank=True)
    is_international_plan = models.BooleanField(default=False)
    is_voice_calling = models.BooleanField(default=False)
    is_insurance = models.BooleanField(default=False)
    first_name = models.CharField(max_length=255, null=True, blank=True)
    last_name = models.CharField(max_length=255, null=True, blank=True)
    user_email = models.CharField(max_length=255, null=True, blank=True)
    employee_id = models.CharField(max_length=255, null=True, blank=True)
    region = models.CharField(max_length=255, null=True, blank=True)
    business_unit = models.CharField(max_length=255, null=True, blank=True)
    gl_code = models.CharField(max_length=255, null=True, blank=True)
    area_code = models.CharField(max_length=255, null=True, blank=True)
    cost_center = models.CharField(max_length=255, null=True, blank=True)
    assigned_user = models.CharField(max_length=255, null=True, blank=True)

    ## Shipping info

    # staging and stepup address
    s_address1 = models.CharField(max_length=255, null=True, blank=True)
    s_address2 = models.CharField(max_length=255, null=True, blank=True)
    s_city = models.CharField(max_length=255, null=True, blank=True)
    s_state = models.CharField(max_length=255, null=True, blank=True)
    s_zipcode = models.CharField(max_length=255, null=True, blank=True)
    # end user address
    e_address1 = models.CharField(max_length=255, null=True, blank=True)
    e_address2 = models.CharField(max_length=255, null=True, blank=True)
    e_city = models.CharField(max_length=255, null=True, blank=True)
    e_state = models.CharField(max_length=255, null=True, blank=True)
    e_zipcode = models.CharField(max_length=255, null=True, blank=True)

    ## office info

    is_remote = models.BooleanField(default=False)
    location_name = models.CharField(max_length=255, null=True, blank=True)
    location_code = models.CharField(max_length=255, null=True, blank=True)
    location_type = models.CharField(max_length=255, null=True, blank=True)
    o_address1 = models.CharField(max_length=255, null=True, blank=True)
    o_address2 = models.CharField(max_length=255, null=True, blank=True)
    o_city = models.CharField(max_length=255, null=True, blank=True)
    o_state = models.CharField(max_length=255, null=True, blank=True)
    o_zipcode = models.CharField(max_length=255, null=True, blank=True)

    notes = models.TextField(null=True, blank=True)

    ## Tracking Infor

    t_device = models.CharField(max_length=255, null=True, blank=True)
    t_username = models.CharField(max_length=255, null=True, blank=True)
    t_mobile = models.CharField(max_length=255, null=True, blank=True)
    imei = models.CharField(max_length=255, null=True, blank=True)
    sim = models.CharField(max_length=255, null=True, blank=True)
    total_cost = models.CharField(max_length=255, null=True, blank=True)
    plan_group = models.CharField(max_length=255, null=True, blank=True)
    etf = models.CharField(max_length=255, null=True, blank=True)
    plan_line_alloc = models.CharField(max_length=255, null=True, blank=True)
    total_per_line = models.CharField(max_length=255, null=True, blank=True)
    vendor_order = models.CharField(max_length=255, null=True, blank=True)
    quote_received_date = models.CharField(max_length=255, null=True, blank=True)
    request_submitted_date = models.CharField(max_length=255, null=True, blank=True)
    request_entered_date = models.CharField(max_length=255, null=True, blank=True)
    shipped_date = models.CharField(max_length=255, null=True, blank=True)
    
    estimated_delivery_date = models.CharField(max_length=255, null=True, blank=True)
    delivery_date = models.CharField(max_length=255, null=True, blank=True)
    delivery_verified = models.BooleanField(default=False)
    activation_verified = models.BooleanField(default=False)
    date_completed = models.DateTimeField(null=True, blank=True)
    suspend_forward_date = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=255, null=True, blank=True, default="Pending")

    is_call_forwarding =  models.BooleanField(default=False)
    forward_to_number= models.CharField(max_length=255, null=True, blank=True)
    forward_to_name= models.CharField(max_length=255, null=True, blank=True)
    is_susped_30_days=  models.BooleanField(default=False)
    upgrade_type=models.CharField(max_length=255, null=True, blank=True)
    device_cost=models.CharField(max_length=255, null=True, blank=True)
    current_number=models.CharField(max_length=255, null=True, blank=True)
    is_new_device=models.BooleanField(default=False)
    authorized_party=models.CharField(max_length=255, null=True, blank=True)
    port_pin = models.CharField(max_length=255, null=True, blank=True)
    other_documents = models.FileField(upload_to='Requests_documents', null=True, blank=True)
    support_type=models.CharField(max_length=255, null=True, blank=True)
    contact_name=models.CharField(max_length=255, null=True, blank=True)
    contact_number=models.CharField(max_length=255, null=True, blank=True)
    contact_description=models.CharField(max_length=255, null=True, blank=True)
    resume_date=models.CharField(max_length=255, null=True, blank=True)
    remark=models.CharField(max_length=255, null=True, blank=True)

    mail_date = models.DateTimeField(null=True, blank=True)
    comment = models.TextField(null=True, blank=True)

    # Remote location
    rl_address1 = models.CharField(max_length=255, null=True, blank=True)
    rl_address2 = models.CharField(max_length=255, null=True, blank=True)
    rl_city = models.CharField(max_length=255, null=True, blank=True)
    rl_state = models.CharField(max_length=255, null=True, blank=True)
    rl_zipcode = models.CharField(max_length=255, null=True, blank=True)

    transfer_type = models.CharField(max_length=255, null=True, blank=True)
    cost_center_add = models.CharField(max_length=255, null=True, blank=True)

    authority_status = models.CharField(max_length=255, default="Pending")
    created = models.DateTimeField(auto_now_add=True, null=True)

    employee_remark = models.TextField(null=True, blank=True)
    client_admin_remark = models.TextField(null=True, blank=True)
    portal_admin_remark = models.TextField(null=True, blank=True)

    updated= models.DateTimeField(auto_now=True,null=True)


    class Meta:
        db_table = 'Requests'


    def __str__(self):
        return self.request_type
    

class TrackingInfo(models.Model):
    request = models.ForeignKey('Requests',on_delete=models.CASCADE, related_name='request_tracking_info')
    shipment_vendor = models.CharField(max_length=255,null=True,blank=True)
    tracking_id = models.CharField(max_length=255,null=True,blank=True,unique=True)
    receipt_details = models.CharField(max_length=255, null=True, blank=True)
    receipt_file = models.FileField(upload_to='request_tracking_files',null=True,blank=True)
    wipe_reset_firmware = models.CharField(max_length=255, null=True, blank=True)
    name_change = models.CharField(max_length=255, null=True, blank=True)
    plan_activity = models.CharField(max_length=255, null=True, blank=True)
    device_status = models.CharField(max_length=255, default=False, null=False)

    created = models.DateTimeField(auto_now_add=True, null=True)
    updated= models.DateTimeField(auto_now=True,null=True)

    class Meta:
        db_table = 'TrackingInfo'

    
class CostCenters(models.Model):
    sub_company = models.ForeignKey(Organizations, on_delete=models.CASCADE,null=False,related_name="sub_company_costcenters")
    vendor = models.ForeignKey(Vendors, related_name="vendor_costcenters", null=False,on_delete=models.CASCADE)
    ban = models.CharField(max_length=255, null=False)
    cost_center = models.CharField(max_length=255, null=False)
    remark = models.TextField(null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True, null=True)
    updated= models.DateTimeField(auto_now=True,null=True)

    class Meta:
        db_table = 'CostCenters'
        constraints = [
            models.UniqueConstraint(fields=['sub_company', 'vendor', 'ban', 'cost_center'], name='unique_cost_center')
        ]



class Device(models.Model):
    sub_company = models.ForeignKey(Organizations, on_delete=models.CASCADE,null=False,related_name="sub_company_devices")
    DEVICE_CHOICES = [
        ("Tablet", "Tablet"),
        ("Smartphone", "Smartphone"),
        ("Accessories", "Accessories")
    ]
    device_type = models.CharField(max_length=255,choices=DEVICE_CHOICES)
    model = models.ForeignKey('MakeModel', on_delete=models.CASCADE, null=False, related_name='models')
    amount = models.FloatField(default=0)
    is_older_model = models.BooleanField(default=False)
    is_default = models.BooleanField(default=False)

    # approved
    is_approved = models.BooleanField(default=False)
    stock_quantity = models.IntegerField(default=0)

    # end of life
    is_expired = models.BooleanField(default=False)
    # damaged
    is_damaged = models.BooleanField(default=False)
    repair_cost = models.FloatField(default=0)

    # individual purchase

    is_individual_purchase = models.BooleanField(default=False)

    # bulk purchase

    order_quantity = models.IntegerField(default=0)
    reorder_quantity = models.IntegerField(default=0)


    created = models.DateTimeField(auto_now_add=True, null=True)
    updated= models.DateTimeField(auto_now=True,null=True)


    class Meta:
        db_table = 'Device'


    def __str__(self):
        return f'{self.device_type}-{self.model}'
    
class MakeModel(models.Model):
    sub_company = models.ForeignKey(Organizations, on_delete=models.CASCADE,null=False,related_name="sub_company_models")
    device_type = models.CharField(max_length=255,null=False)
    accessory = models.CharField(max_length=255, null=True,blank=True)
    name = models.CharField(max_length=255, null=False)
    os = models.CharField(max_length=255, null=True,blank=True)
    storage = models.CharField(max_length=100, null=True, blank=True)
    color = models.CharField(max_length=100, null=True, blank=True)
    manufacturer = models.CharField(max_length=100, null=True, blank=True)
    other_specifications = models.JSONField(default=dict)
    created = models.DateTimeField(auto_now_add=True, null=True)
    updated= models.DateTimeField(auto_now=True,null=True)


    class Meta:
        db_table = 'MakeModel'
        constraints = [
            models.UniqueConstraint(fields=['sub_company', 'device_type', 'name'], name='unique_model')
        ]


class VendorDevice(models.Model):
    sub_company = models.ForeignKey(Organizations, on_delete=models.CASCADE,null=False,related_name="sub_company_vendor_devices")
    model = models.ForeignKey('MakeModel', on_delete=models.CASCADE, null=False, related_name='vendor_device_models')
    vendor = models.ForeignKey(Vendors, related_name="vendor_devices", null=False,on_delete=models.CASCADE)
    retail_price = models.FloatField(default=0)
    discounted_price = models.FloatField(default=0)
    is_payment_plan = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True, null=True)
    updated= models.DateTimeField(auto_now=True,null=True)


    class Meta:
        db_table = 'VendorDevice'

class VendorPlan(models.Model):
    sub_company = models.ForeignKey(Organizations, on_delete=models.CASCADE,null=False,related_name="sub_company_vendor_plans")
    vendor = models.ForeignKey(Vendors, related_name="vendor_plans", null=False,on_delete=models.CASCADE)
    ban = models.CharField(max_length=20, null=False)
    plan = models.CharField(max_length=255, null=False)
    plan_type = models.CharField(max_length=255, null=True, blank=True)
    data_allotment = models.CharField(max_length=255, null=True, blank=True)
    plan_fee = models.FloatField(default=0)
    smartphone = models.FloatField(default=0)
    tablet_computer = models.FloatField(default=0)
    mifi = models.FloatField(default=0)
    wearables = models.FloatField(default=0)

    created = models.DateTimeField(auto_now_add=True, null=True)
    updated= models.DateTimeField(auto_now=True,null=True)

    class Meta:
        db_table = 'VendorPlan'
        constraints = [
            models.UniqueConstraint(fields=['sub_company', 'vendor', 'ban','plan'], name='unique_vendor_plan')
        ]

    

class VendorInformation(models.Model):
    sub_company = models.ForeignKey(Organizations, on_delete=models.CASCADE,null=False,related_name="sub_company_vendor_info")
    vendor = models.ForeignKey(Vendors, related_name="vendor_information", null=False,on_delete=models.CASCADE)
    ban = models.CharField(max_length=20, null=False)

    # either existing plan or vendor plan
    existing_plan = models.CharField(max_length=255, null=True, blank=True)
    vendor_plan = models.ForeignKey(VendorPlan, related_name="vendor_information_plans",null=True, on_delete=models.SET_NULL)

    code = models.CharField(max_length=255, null=True, blank=True)
    sales_rep_name = models.CharField(max_length=255, null=True, blank=True)
    sales_rep_email = models.EmailField(max_length=255, null=True, blank=True)
    sales_rep_phone = models.CharField(max_length=12, null=True, blank=True)
    tech_support_phone = models.CharField(max_length=12, null=True, blank=True)
    tech_support_email = models.EmailField(max_length=255, null=True, blank=True)
    order_support_phone = models.CharField(max_length=12, null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True, null=True)
    updated= models.DateTimeField(auto_now=True,null=True)
    single_point_contact = models.CharField(max_length=255, null=True, blank=True)
    is_international_plan = models.BooleanField(default=False)
    is_voip_calling = models.BooleanField(default=False)
    is_insurance = models.BooleanField(default=False)
    is_default = models.BooleanField(default=False)
    baseline_object = models.JSONField(default=list)

    plan_replaced_with = models.CharField(max_length=255, null=True, blank=True)

    request_type = models.CharField(max_length=255, null=True, blank=True)
    request_file = models.FileField(upload_to='vendor_information_files', null=True, blank=True)

    created = models.DateTimeField(auto_now_add=True, null=True)
    updated= models.DateTimeField(auto_now=True,null=True)

    class Meta:
        db_table = 'VendorInformation'
        constraints = [
            models.UniqueConstraint(fields=['sub_company', 'vendor', 'ban','vendor_plan'], name='unique_vendor_information')
        ]

class upgrade_device_request(models.Model):
    organization = models.ForeignKey(Organizations, related_name="upgrade_reuqest_organizations", null=True,on_delete=models.CASCADE)
    vendor = models.ForeignKey(Vendors, related_name="upgrade_reuqest_vendors", null=True,on_delete=models.CASCADE)
    raised_by = models.ForeignKey(PortalUser, on_delete=models.CASCADE, related_name="upgrade_device_by_user")
    sub_company = models.ForeignKey(Organizations, on_delete=models.CASCADE,null=False,related_name="sub_company_upgrade_request")
    wireless_number = models.CharField(max_length=15, null=False)
    device_type = models.CharField(max_length=255, null=True, blank=True)
    manufacturer = models.CharField(max_length=255, null=True, blank=True)
    user_name = models.CharField(max_length=255, null=True, blank=True)
    request_type = models.CharField(max_length=255,default="upgrade_device_request")
    request_date = models.DateTimeField(default=timezone.now, null=True, blank=True)
    model = models.CharField(max_length=255, null=True, blank=True)
    os = models.CharField(max_length=255, null=True, blank=True)
    color = models.CharField(max_length=255, null=True, blank=True)
    serial_number = models.CharField(max_length=255, null=True, blank=True)
    storage = models.CharField(max_length=255, null=True, blank=True)
    imei_number = models.CharField(max_length=255, null=True, blank=True)
    device_etf = models.CharField(max_length=255, null=True, blank=True)
    mobile_device = models.CharField(max_length=255, null=True, blank=True)
    mifi = models.CharField(max_length=255, null=True, blank=True)
    smartphone = models.CharField(max_length=255, null=True, blank=True)
    tablet = models.CharField(max_length=255, null=True, blank=True)
    wearables = models.CharField(max_length=255, null=True, blank=True)
    device_type = models.CharField(max_length=255, null=True, blank=True)
    new_upgrade_date = models.DateField(null=True, blank=True)
    amount = models.CharField(max_length=255, null=True, blank=True)
    status = models.CharField(default="Pending", max_length=255)
    authority_status = models.CharField(max_length=255, default="Pending")
    date_completed = models.DateTimeField(null=True, blank=True)

    employee_remark = models.TextField(null=True, blank=True)
    client_admin_remark = models.TextField(null=True, blank=True)
    portal_admin_remark = models.TextField(null=True, blank=True)

    created = models.DateTimeField(auto_now_add=True, null=True)
    updated= models.DateTimeField(auto_now=True,null=True)

    class Meta:
        db_table = 'upgrade_device_request'
    def save(self, *args, **kwargs):
        if self.raised_by:
            self.user_name = self.raised_by.username  # auto-set
        super().save(*args, **kwargs)


    
class AccessoriesRequest(models.Model):
    organization = models.ForeignKey(Organizations, related_name="acc_reuqest_organizations", null=False,on_delete=models.CASCADE)
    requester = models.ForeignKey(PortalUser, related_name="acc_reuqest_users", null=False,on_delete=models.CASCADE)
    user_name = models.CharField(max_length=255, null=True, blank=True)
    REQUEST_CHOICES = [
        ("Order", "Order"),
        ("Replace", "Replace"),
        ("Return", "Return")
    ]
    request_type = models.CharField(max_length=255,choices=REQUEST_CHOICES)
    shipping_method = models.CharField(max_length=200, default="", null=True, blank=True)
    request_date = models.DateTimeField(default=timezone.now, null=True, blank=True)
    vendor = models.ForeignKey(Vendors, related_name="acc_reuqest_vendors", null=False,on_delete=models.CASCADE)
    ban = models.CharField(max_length=255, null=False,default="")
    line_of_service = models.CharField(max_length=15, null=False, default="123-456-7890")
    accessory_type = models.CharField(max_length=255, null=False,default="")
    manufacturer = models.CharField(max_length=255, null=False,default="")
    name = models.CharField(max_length=255, null=False,default="")
    other_specifications = models.JSONField(default=dict)


    ## requester information

    first_name = models.CharField(max_length=255, null=True, blank=True)
    last_name = models.CharField(max_length=255, null=True, blank=True)
    user_email = models.CharField(max_length=255, null=True, blank=True)
    area_code = models.CharField(max_length=255, null=True, blank=True)
    cost_center = models.CharField(max_length=255, null=True, blank=True)

    ## pickup address

    o_address1 = models.CharField(max_length=255, null=True, blank=True)
    o_address2 = models.CharField(max_length=255, null=True, blank=True)
    o_city = models.CharField(max_length=255, null=True, blank=True)
    o_state = models.CharField(max_length=255, null=True, blank=True)
    o_zipcode = models.CharField(max_length=255, null=True, blank=True)

    ## office info

    is_remote = models.BooleanField(default=False)
    location_name = models.CharField(max_length=255, null=True, blank=True)
    location_code = models.CharField(max_length=255, null=True, blank=True)
    location_type = models.CharField(max_length=255, null=True, blank=True)
    p_address1 = models.CharField(max_length=255, null=True, blank=True)
    p_address2 = models.CharField(max_length=255, null=True, blank=True)
    p_city = models.CharField(max_length=255, null=True, blank=True)
    p_state = models.CharField(max_length=255, null=True, blank=True)
    p_zipcode = models.CharField(max_length=255, null=True, blank=True)

    rl_address1 = models.CharField(max_length=255, null=True, blank=True)
    rl_address2 = models.CharField(max_length=255, null=True, blank=True)
    rl_city = models.CharField(max_length=255, null=True, blank=True)
    rl_state = models.CharField(max_length=255, null=True, blank=True)
    rl_zipcode = models.CharField(max_length=255, null=True, blank=True)

    shipping_vendor = models.CharField(max_length=255, null=True, blank=True)
    tracking_id = models.CharField(max_length=255, null=True, blank=True)
    shipping_date = models.CharField(max_length=255, null=True, blank=True)
    estimated_delivery_date = models.CharField(max_length=255, null=True, blank=True)
    delivery_date = models.CharField(max_length=255, null=True, blank=True)
    receipt_id = models.CharField(max_length=255, null=True, blank=True)

    replacement_tracking_id = models.CharField(max_length=255, null=True, blank=True)
    replacement_delivery_date = models.CharField(max_length=255, null=True, blank=True)
    replacement_reason = models.CharField(max_length=255, null=True, blank=True)

    return_tracking_id = models.CharField(max_length=255, null=True, blank=True)
    return_shipped_date = models.CharField(max_length=255, null=True, blank=True)
    return_received_date = models.CharField(max_length=255, null=True, blank=True)
    return_reason = models.CharField(max_length=255, null=True, blank=True)
    notes = models.TextField(null=True, blank=True)



    date_completed = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=255, null=True, blank=True, default="Pending")
    authority_status = models.CharField(max_length=255, default="Pending")

    employee_remark = models.TextField(null=True, blank=True)
    client_admin_remark = models.TextField(null=True, blank=True)
    portal_admin_remark = models.TextField(null=True, blank=True)

    created = models.DateTimeField(auto_now_add=True, null=True)
    updated= models.DateTimeField(auto_now=True,null=True)

    class Meta:
        db_table = 'AccessoriesRequest'
    def save(self, *args, **kwargs):
        if self.requester:
            self.user_name = self.requester.username 
        super().save(*args, **kwargs)
