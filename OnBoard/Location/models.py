from django.db import models
from ..Organization.models import Organizations, Division
from..Company.models import Company


class BulkLocation(models.Model):
    organization = models.ForeignKey(
        Organizations, related_name='bulk', on_delete=models.CASCADE, null=True, blank=True
    )
    file = models.FileField(upload_to='bulk_upload_location', blank=True, null=True, default=None)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'BulkLocation'

    def __str__(self):
        return f'Bulk Location - {self.bulk_upload_file.name}'
    
class Location(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, default=None, null=True, blank=True)
    organization = models.ForeignKey(
        Organizations, related_name='locations', on_delete=models.CASCADE
    )
    location_type = models.CharField(max_length=255)
    end_user = models.CharField(max_length=255, blank=True, null=True)
    end_user_billing = models.CharField(max_length=255, blank=True, null=True)
    physical_address = models.CharField(max_length=255)
    country = models.CharField(max_length=255)
    physical_city = models.CharField(max_length=255, blank=True, null=True)
    state = models.CharField(max_length=255)
    physical_zip_code = models.CharField(max_length=255, blank=True, null=True)
    mail_address = models.CharField(max_length=255)
    mail_city = models.CharField(max_length=255)
    mail_state = models.CharField(max_length=255)
    mail_zip_code = models.CharField(max_length=255)
    division = models.ForeignKey(Division, null=True, blank=True, on_delete=models.SET_NULL)
    region = models.CharField(max_length=255, blank=True, null=True)
    district = models.CharField(max_length=255, blank=True, null=True)
    site_name = models.CharField(max_length=255)
    alias = models.CharField(max_length=255, blank=True, null=True)
    primary_email = models.EmailField(max_length=255)
    secondary_email = models.EmailField(max_length=255, blank=True, null=True)
    main_phone_code = models.CharField(max_length=255)
    main_phone = models.CharField(max_length=255)
    main_fax_code = models.CharField(max_length=255, blank=True, null=True)
    main_fax = models.CharField(max_length=255, blank=True, null=True)
    location_tax_id = models.CharField(max_length=255, blank=True, null=True)
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    title = models.CharField(max_length=255, blank=True, null=True)
    did_number_code = models.CharField(max_length=255)
    did_number = models.CharField(max_length=255)
    extension = models.CharField(max_length=255, blank=True, null=True)
    mobile_code = models.CharField(max_length=255)
    mobile_number = models.CharField(max_length=255)
    mobile_status = models.CharField(max_length=255)
    notes = models.TextField(blank=True, null=True)

    location_picture_1 = models.FileField(upload_to='location_pictures/', blank=True, null=True)
    location_picture_2 = models.FileField(upload_to='location_pictures/', blank=True, null=True)
    location_picture_3 = models.FileField(upload_to='location_pictures/', blank=True, null=True)
    location_picture_4 = models.FileField(upload_to='location_pictures/', blank=True, null=True)

    bulkfile = models.ForeignKey(BulkLocation, null=True, blank=True, default=None, related_name='bulk_uploads', on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'Location'
        constraints = [
            models.UniqueConstraint(fields=['company', 'organization', 'site_name'], name='unique_location')
        ]

    def __str__(self):
        return self.site_name

