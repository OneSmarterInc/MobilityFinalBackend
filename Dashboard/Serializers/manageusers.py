from rest_framework import serializers
from OnBoard.Company.models import Company
from authenticate.models import PortalUser
from ..ModelsByPage.DashAdmin import UserRoles
from OnBoard.Organization.models import Organizations
class showcompaniesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = ['Company_name',]

class UserRoleShowSerializer(serializers.ModelSerializer):
    # permissions = serializers.StringRelatedField(many=True)
    class Meta:
        model = UserRoles
        fields = ['name','id']

class userSerializer(serializers.ModelSerializer):
    company = serializers.CharField()
    designation = UserRoleShowSerializer()
    class Meta:
        model = PortalUser
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'company', 'designation', 'mobile_number', 'phone_number']

class showOrgsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organizations
        fields = ['Organization_name','id']