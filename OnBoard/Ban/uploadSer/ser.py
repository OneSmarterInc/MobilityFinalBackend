from rest_framework import serializers
from ..models import UploadBAN, OnboardBan, InventoryUpload, BaseDataTable
from Dashboard.ModelsByPage.DashAdmin import Vendors, EntryType, BanStatus, BanType, InvoiceMethod, PaymentType, CostCenterLevel, CostCenterType, BillType
from ...Organization.models import Organizations
from ...Company.models import Company
from ...Location.models import Location

class BanshowSerializer(serializers.ModelSerializer):
    class Meta:
        model = BaseDataTable
        fields = ['accountnumber','vendor']

class OrganizationShowuploadSerializer(serializers.ModelSerializer):
    locations = serializers.StringRelatedField(many=True)
    company = serializers.CharField(max_length=255, read_only=True)
    vendors = serializers.StringRelatedField(many=True)

    class Meta:
        model = Organizations
        fields = ['id', 'Organization_name', 'locations', 'company','vendors']
    
    def get_vendors(self, obj):
        return [vendor.name for vendor in obj.vendors.all()]

    
    def get_locations(self, obj):
        return [location.site_name for location in obj.locations.all()]
    
    # def get_bans(self, obj):
    #     return [ban.account_number for ban in UploadBAN.objects.filter(organization=obj)]
    
    def get_company(self, obj):
        return obj.company.Company_name
    
class CompanyShowSerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = ['Company_name',]

class VendorShowSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vendors
        fields = ['name',]

class BanStatusShowSerializer(serializers.ModelSerializer):
    class Meta:
        model = BanStatus
        fields = ['name',]

class BanTypeShowSerializer(serializers.ModelSerializer):
    class Meta:
        model = BanType
        fields = ['name',]

class InvoiceMethodShowSerializer(serializers.ModelSerializer):
    class Meta:
        model = InvoiceMethod
        fields = ['name',]


class PaymentTypeShowSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentType
        fields = ['name',]


class CostCenterLevelShowSerializer(serializers.ModelSerializer):
    class Meta:
        model = CostCenterLevel
        fields = ['name',]


class CostCenterTypeShowSerializer(serializers.ModelSerializer):
    class Meta:
        model = CostCenterType
        fields = ['name',]



