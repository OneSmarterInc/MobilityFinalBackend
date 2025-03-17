from django.db import models
from django.utils import timezone

class Vendors(models.Model):
    name = models.CharField(max_length=255, unique=True)
    vendor_logo = models.ImageField(upload_to='vendor_logos/', null=True, blank=True)
    home_page = models.URLField(max_length=200, null=True, blank=True)
    company_overview = models.TextField(null=True, blank=True)
    customer_portal_url = models.URLField(max_length=200, null=True, blank=True)
    review = models.TextField(null=True, blank=True)
    customer_support_email = models.EmailField(max_length=255, null=True, blank=True)
    customer_support_phone = models.CharField(max_length=20, null=True, blank=True)

    # Rating fields
    reliability = models.FloatField(default=0.0)
    pricing = models.FloatField(default=0.0)
    user_friendly = models.FloatField(default=0.0)
    support = models.FloatField(default=0.0)
    features = models.FloatField(default=0.0)
    created = models.DateTimeField(null=False, auto_now_add=True)
    updated = models.DateTimeField(null=True, blank=True, auto_now=True)
    
    class Meta:
        db_table = 'Vendors'

    def __str__(self):
        return self.name
    
class EntryType(models.Model):
    name = models.CharField(max_length=255, unique=True)
    created = models.DateTimeField(null=False, auto_now_add=True)
    updated = models.DateTimeField(null=True, blank=True, auto_now=True)

    class Meta:
        db_table = 'EntryType'

    def __str__(self):
        return self.name
    
class BanStatus(models.Model):
    name = models.CharField(max_length=255, unique=True)
    created = models.DateTimeField(null=False, auto_now_add=True)
    updated = models.DateTimeField(null=True, blank=True, auto_now=True)

    class Meta:
        db_table = 'BanStatus'

    def __str__(self):
        return self.name
    
class InvoiceMethod(models.Model):
    name = models.CharField(max_length=255, unique=True)
    created = models.DateTimeField(null=False, auto_now_add=True)
    updated = models.DateTimeField(null=True, blank=True, auto_now=True)

    class Meta:
        db_table = 'InvoiceMethod'

    def __str__(self):
        return self.name
    
class BanType(models.Model):
    name = models.CharField(max_length=255, unique=True)
    created = models.DateTimeField(null=False, auto_now_add=True)
    updated = models.DateTimeField(null=True, blank=True, auto_now=True)

    class Meta:
        db_table = 'BanType'

    def __str__(self):
        return self.name
    
class PaymentType(models.Model):
    name = models.CharField(max_length=255, unique=True)
    created = models.DateTimeField(null=False, auto_now_add=True)
    updated = models.DateTimeField(null=True, blank=True, auto_now=True)

    class Meta:
        db_table = 'PaymentType'

    def __str__(self):
        return self.name
    
class CostCenterLevel(models.Model):
    name = models.CharField(max_length=255, unique=True)
    created = models.DateTimeField(null=False, auto_now_add=True)
    updated = models.DateTimeField(null=True, blank=True, auto_now=True)

    class Meta:
        db_table = 'CostCenterLevel'

    def __str__(self):
        return self.name
    
class CostCenterType(models.Model):
    name = models.CharField(max_length=255, unique=True)
    created = models.DateTimeField(null=False, auto_now_add=True)
    updated = models.DateTimeField(null=True, blank=True, auto_now=True)

    class Meta:
        db_table = 'CostCenterType'

    def __str__(self):
        return self.name
    
class Permission(models.Model):
    Type = models.CharField(max_length=255, default="Default")
    name = models.CharField(max_length=255, unique=True)
    created = models.DateTimeField(null=False, auto_now_add=True)
    updated = models.DateTimeField(null=True, blank=True, auto_now=True)

    class Meta:
        db_table = 'Permission'

    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if self.Type:
            self.Type = self.Type.capitalize()
        super(Permission, self).save(*args, **kwargs)
    
class UserRoles(models.Model):
    name = models.CharField(max_length=255, unique=True)
    created = models.DateTimeField(null=False, auto_now_add=True)
    updated = models.DateTimeField(null=True, blank=True, auto_now=True)
    
    permissions = models.ManyToManyField(Permission, related_name='roles')
    class Meta:
        db_table = 'UserRoles'

class ManuallyAddedLocation(models.Model):
    name = models.CharField(max_length=255, unique=True)
    created = models.DateTimeField(null=False, auto_now_add=True)
    updated = models.DateTimeField(null=True, blank=True, auto_now=True)

    class Meta:
        db_table = 'ManuallyAddedLocation'

    def __str__(self):
        return self.name
    
class ManuallyAddedCompany(models.Model):
    name = models.CharField(max_length=255, unique=True)
    created = models.DateTimeField(null=False, auto_now_add=True)
    updated = models.DateTimeField(null=True, blank=True, auto_now=True)

    class Meta:
        db_table = 'ManuallyAddedCompany'

    def __str__(self):
        return self.name
    
class BillType(models.Model):
    name = models.CharField(max_length=255, unique=True)
    created = models.DateTimeField(null=False, auto_now_add=True)
    updated = models.DateTimeField(null=True, blank=True, auto_now=True)

    class Meta:
        db_table = 'BillType'

    def __str__(self):
        return self.name