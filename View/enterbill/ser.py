from rest_framework import serializers
from OnBoard.Organization.models import Organizations
from Dashboard.ModelsByPage.DashAdmin import Vendors
from OnBoard.Ban.models import UploadBAN, BaseDataTable, UniquePdfDataTable, BaselineDataTable
from ..models import viewPaperBill

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
    
class showBanSerializer(serializers.ModelSerializer):
    organization = serializers.CharField(max_length=255)
    Vendor = serializers.CharField(max_length=255)
    class Meta:
        model = UploadBAN
        fields = ['account_number','organization', 'Vendor']


class BaselineDataTableShowSerializer(serializers.ModelSerializer):
    # banOnboarded = serializers.CharField(max_length=255)
    class Meta:
        model = BaselineDataTable
        fields = '__all__'
    

class viewPaperBillserializer(serializers.ModelSerializer):
    company = serializers.CharField()
    organization = serializers.CharField()
    vendor = serializers.CharField()
    class Meta:
        model = viewPaperBill
        fields = '__all__'
class showOnboardedSerializer(serializers.ModelSerializer):
    class Meta:
        model = BaseDataTable
        fields = "__all__"

