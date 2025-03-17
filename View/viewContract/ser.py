from rest_framework import serializers
from OnBoard.Organization.models import Organizations, Contract
from OnBoard.Ban.models import UploadBAN, BaseDataTable, UniquePdfDataTable
from Dashboard.ModelsByPage.DashAdmin import Vendors

class showContractSerializer(serializers.ModelSerializer):
    organization = serializers.CharField(max_length=255)
    vendor = serializers.CharField(max_length=255)
    class Meta:
        model = Contract
        fields = '__all__'

class showOrganizationSerializer(serializers.ModelSerializer):
    vendors = serializers.StringRelatedField(many=True)
    class Meta:
        model = Organizations
        fields = ['Organization_name', 'vendors', 'contract_file', 'contract_name', 'created', 'contract']

class vendorshowSerializer(serializers.ModelSerializer):
    name = serializers.CharField(max_length=255)
    class Meta:
        model = Vendors
        fields = ['name',]




