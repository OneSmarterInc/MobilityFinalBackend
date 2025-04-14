from django.db import models
class BaselineCategories(models.Model):
    category = models.CharField(max_length=255, null=False, unique=True)
    sub_categories =  models.JSONField(null=True, default=list)
    
    class Meta:
        db_table = 'BaselineCategories'

    def __str__(self):
        return self.category