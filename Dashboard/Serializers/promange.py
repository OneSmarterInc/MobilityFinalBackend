from rest_framework import serializers
from OnBoard.Ban.models import UniquePdfDataTable
from ..ModelsByPage.DashAdmin import UserRoles
from OnBoard.Organization.models import Organizations
from authenticate.models import PortalUser
class OrganizationsShowSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organizations
        fields = ['id', 'Organization_name',]
        
class showdesignations(serializers.ModelSerializer):
    class Meta:
        model = UserRoles
        fields = '__all__'

class showrolename(serializers.ModelSerializer):
    class Meta:
        model = UserRoles
        fields = ['name',]
class showusers(serializers.ModelSerializer):
    designation = showrolename()
    class Meta:
        model = PortalUser
        fields = ['first_name', 'last_name','id','designation','username','contact_type', 'email','phone_number','mobile_number']
