from django.db import models
from OnBoard.Organization.models import Organizations
from Dashboard.ModelsByPage.DashAdmin import Vendors
from OnBoard.Ban.models import BaseDataTable
class BaselineCategories(models.Model):
    
    organization = models.ForeignKey(Organizations, related_name="categories_organizations", null=True,on_delete=models.CASCADE)
    vendor = models.ForeignKey(Vendors, related_name="categories_vendors", null=True,on_delete=models.CASCADE)
    ban = models.CharField(max_length=255, null=False,default="")
    banObj = models.ForeignKey(BaseDataTable, on_delete=models.CASCADE, null=True, blank=True)
    category = models.CharField(max_length=255, null=False)
    sub_categories =  models.JSONField(null=True, default=list)
    
    class Meta:
        db_table = 'BaselineCategories'
        unique_together = (('organization', 'vendor','banObj','category'))

    def __str__(self):
        return f'{self.organization}-{self.vendor}-{self.ban}-{self.category}'
    def save(self, *args, **kwargs):
        if not self.banObj and (self.organization and self.vendor and self.ban):
            self.banObj = BaseDataTable.objects.exclude(banUploaded=None, banOnboarded=None).filter(sub_company=self.organization.Organization_name, vendor=self.vendor.name, accountnumber=self.ban).first()
            pass
        super().save(*args, **kwargs)