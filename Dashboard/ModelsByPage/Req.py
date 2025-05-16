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

    ## Accessories
    cases = models.CharField(max_length=255, null=True, blank=True)
    screen_protector = models.CharField(max_length=255, null=True, blank=True)
    features = models.JSONField(default=list, null=True, blank=True)
    is_international_plan = models.BooleanField(default=False)
    is_voice_calling = models.BooleanField(default=False)
    is_insurace = models.BooleanField(default=False)
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
    tracking_id = models.CharField(max_length=255, null=True, blank=True)
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

    created = models.DateTimeField(auto_now_add=True, null=True)
    updated= models.DateTimeField(auto_now=True,null=True)


    class Meta:
        db_table = 'Requests'


    def __str__(self):
        return self.mobile
