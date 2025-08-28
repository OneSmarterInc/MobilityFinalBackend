from django.db import models
from OnBoard.Organization.models import Organizations
from Dashboard.ModelsByPage.DashAdmin import Vendors
class BaselineCategories(models.Model):
    
    organization = models.ForeignKey(Organizations, related_name="categories_organizations", null=True,on_delete=models.CASCADE)
    vendor = models.ForeignKey(Vendors, related_name="categories_vendors", null=True,on_delete=models.CASCADE)
    ban = models.CharField(max_length=255, null=False,default="")
    category = models.CharField(max_length=255, null=False, unique=True)
    sub_categories =  models.JSONField(null=True, default=list)
    
    class Meta:
        db_table = 'BaselineCategories'
        unique_together = (('organization', 'vendor','ban','category'))

    def __str__(self):
        return self.category