from rest_framework import serializers
from ..ModelsByPage.Req import Requests
from OnBoard.Organization.models import Organizations
from authenticate.models import PortalUser
from Dashboard.ModelsByPage.DashAdmin import Vendors
from OnBoard.Ban.models import BaseDataTable, UniquePdfDataTable



class showOrganizations(serializers.ModelSerializer):
    class Meta:
        model = Organizations
        fields = ('Organization_name','id')

class showUsers(serializers.ModelSerializer):
    class Meta:
        model = PortalUser
        fields = ('id','first_name','last_name','email')


    
class OrganizationShowSerializer(serializers.ModelSerializer):
    vendors = serializers.StringRelatedField(many=True)
    locations = serializers.StringRelatedField(many=True)

    class Meta:
        model = Organizations
        fields = ['id', 'Organization_name', 'vendors', 'locations']


class VendorShowSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vendors
        fields = ['name',]

class showOnboardedSerializer(serializers.ModelSerializer):
    class Meta:
        model = BaseDataTable
        fields = ['accountnumber','vendor','sub_company']

class showRequestSerializer(serializers.ModelSerializer):
    organization = OrganizationShowSerializer()
    requester = showUsers()
    vendor = VendorShowSerializer()
    class Meta:
        model = Requests
        fields = '__all__'

from django.utils.dateparse import parse_datetime

class RequestsSaveSerializer(serializers.ModelSerializer):
    class Meta:
        model = Requests
        fields = '__all__'

class UniquePdfShowSerializer(serializers.ModelSerializer):
    class Meta:
        model = UniquePdfDataTable
        fields = ('user_name','account_number','vendor','sub_company','wireless_number')