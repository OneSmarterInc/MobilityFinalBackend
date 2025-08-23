from django.db import models
from OnBoard.Organization.models import Organizations
from authenticate.models import PortalUser
from Dashboard.admin import Vendors
from .DashAdmin import UserRoles, Permission
class Profile(models.Model):
    organization = models.ForeignKey(Organizations, related_name="organizations", null=False,on_delete=models.CASCADE)
    usertype = models.IntegerField(default=0, null=True, blank=True)
    user = models.ForeignKey(PortalUser, related_name='users', null=False,on_delete=models.CASCADE)
    role = models.ForeignKey(UserRoles, related_name='roles',on_delete=models.CASCADE, null=True)
    email = models.EmailField(max_length=255, null=True, blank=True)
    phone = models.CharField(max_length=12, null=True, blank=True)
    vendors = models.ManyToManyField(Vendors, related_name='profile_vendors')
    permissions = models.ManyToManyField(Permission, related_name='permissions',blank=True)

    class Meta:
        db_table = "Profile"
        constraints = [
            models.UniqueConstraint(fields=['organization', 'usertype', 'user'], name='unique_profile')
        ]

    def __str__(self):
        return f'{self.organization}-{self.user}'
