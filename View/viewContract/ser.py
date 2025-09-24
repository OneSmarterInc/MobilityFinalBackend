from rest_framework import serializers
from OnBoard.Organization.models import Organizations
from ..models import Contracts
from OnBoard.Ban.models import UploadBAN, BaseDataTable, UniquePdfDataTable, OnboardBan
from Dashboard.ModelsByPage.DashAdmin import Vendors



class showContractSerializer(serializers.ModelSerializer):

    sub_company = serializers.SerializerMethodField()
    account_number = serializers.SerializerMethodField()
    vendor = serializers.SerializerMethodField()
    class Meta:
        model = Contracts
        fields = '__all__'
    def get_sub_company(self,obj):
        if obj.onboardedban: return obj.onboardedban.organization.Organization_name
        if obj.uploadedban: return obj.uploadedban.organization.Organization_name
    def get_account_number(self,obj):
        if obj.onboardedban: return obj.onboardedban.account_number
        if obj.uploadedban: return obj.uploadedban.account_number
    def get_vendor(self,obj):
        if obj.onboardedban: return obj.onboardedban.vendor.name
        if obj.uploadedban: return obj.uploadedban.Vendor.name

    

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


