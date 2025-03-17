from rest_framework import serializers
from OnBoard.Company.models import Company
from authenticate.models import PortalUser
from ..ModelsByPage.DashAdmin import UserRoles
class showcompaniesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = ['Company_name',]

class UserRoleShowSerializer(serializers.ModelSerializer):
    # permissions = serializers.StringRelatedField(many=True)
    class Meta:
        model = UserRoles
        fields = ['name',]

class userSerializer(serializers.ModelSerializer):
    company = serializers.CharField()
    designation = UserRoleShowSerializer()
    class Meta:
        model = PortalUser
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'company', 'designation', 'mobile_number', 'phone_number']
    
