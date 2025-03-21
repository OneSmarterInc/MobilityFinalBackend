from rest_framework import serializers
from ..models import UploadBAN, BaseDataTable
from ...Organization.models import Organizations


class OrganizationShowSerializer(serializers.ModelSerializer):
    vendors = serializers.StringRelatedField(many=True)
    bans = serializers.SerializerMethodField()
    company = serializers.CharField(max_length=255, read_only=True)

    class Meta:
        model = Organizations
        fields = ['id', 'Organization_name', 'vendors', 'bans', 'company']


    def get_vendors(self, obj):
        return [vendor.name for vendor in obj.vendors.all()]
    
    def get_bans(self, obj):
        return [ban.account_number for ban in UploadBAN.objects.filter(organization=obj)]
    
    def get_company(self, obj):
        return obj.company.Company_name
    
class showBaseDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = BaseDataTable
        fields = ['company','accountnumber','vendor','master_account','sub_company']

class BanShowSerializer(serializers.ModelSerializer):
    class Meta:
        model = UploadBAN
        fields = ['id','account_number','company', 'organization', 'Vendor']

    company = serializers.CharField()
    organization = serializers.CharField()
    Vendor = serializers.CharField()
    