from rest_framework import serializers
from OnBoard.Organization.models import Organizations
from ..models import Contracts
from OnBoard.Ban.models import UploadBAN, BaseDataTable, UniquePdfDataTable
from Dashboard.ModelsByPage.DashAdmin import Vendors


class uploadaccountser(serializers.ModelSerializer):
    organization = serializers.CharField(max_length=255)
    Vendor = serializers.CharField(max_length=255)
    class Meta:
        model = UploadBAN
        fields = ['account_number', 'Vendor', 'organization']

class baseaccser(serializers.ModelSerializer):
    organization = serializers.CharField(max_length=255)
    vendor = serializers.CharField(max_length=255)
    class Meta:
        model = BaseDataTable
        fields = ['accountnumber', 'vendor', 'organization']

class showContractSerializer(serializers.ModelSerializer):
    baseban = baseaccser()
    uploadedban = uploadaccountser()
    class Meta:
        model = Contracts
        fields = '__all__'


class showOrganizationSerializer(serializers.ModelSerializer):
    vendors = serializers.StringRelatedField(many=True)
    class Meta:
        model = Organizations
        fields = ['Organization_name', 'vendors', 'contract_file', 'contract_name', 'created']

class vendorshowSerializer(serializers.ModelSerializer):
    name = serializers.CharField(max_length=255)
    class Meta:
        model = Vendors
        fields = ['name',]

class saveContractSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Contracts
        fields = '__all__'


