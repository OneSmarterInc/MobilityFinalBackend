from rest_framework import serializers
from OnBoard.Company.models import Company
from OnBoard.Organization.models import Organizations
from OnBoard.Location.models import Location
from Dashboard.ModelsByPage.DashAdmin import Vendors, EntryType
from OnBoard.Ban.models import UploadBAN, OnboardBan, BaseDataTable, Lines, UniquePdfDataTable, BaselineDataTable

class CompanygetNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = ['Company_name']




class OrganizationgetNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organizations
        fields = ['Organization_name']



class LocationGetNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = ['site_name']

class LocationGetAllDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = '__all__'

class VendorNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vendors
        fields = ['name']

class VendorGetAllDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vendors
        fields = '__all__'
from OnBoard.Ban.PortalInfo.ser import showPortalInfoser

class OrganizationGetAllDataSerializer(serializers.ModelSerializer):
    vendors = VendorNameSerializer(many=True)
    company = CompanygetNameSerializer()
    # divisions = serializers.StringRelatedField(many=True)
    divisions = serializers.SerializerMethodField()
    class Meta:
        model = Organizations
        fields = '__all__'
    def get_divisions(self,obj):
        divs = obj.divisions.all()
        return [{"id":div.id, "name":div.name} for div in divs]

    

class CompanygetAllDataSerializer(serializers.ModelSerializer):
    vendors = VendorNameSerializer(many=True)
    class Meta:
        model = Company
        fields = '__all__'


class EntryTypeGetNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = EntryType
        fields = ('name', )

class CompanyShowSerializer(serializers.ModelSerializer):

    class Meta:
        model = Company
        fields = '__all__'

from collections import defaultdict

class UploadBANSerializer(serializers.ModelSerializer):
    class Meta:
        model = UploadBAN
        fields = '__all__'

    entryType = serializers.CharField()
    masteraccount = serializers.CharField()
    banstatus = serializers.CharField()
    account_number = serializers.CharField()
    Vendor = serializers.CharField()
    location = serializers.CharField()
    organization = serializers.CharField()
    company = serializers.CharField()
    bantype  = serializers.CharField()
    invoicemethod = serializers.CharField()
    paymenttype = serializers.CharField()
    costcenterlevel = serializers.CharField()
    costcentertype = serializers.CharField()
    user_email = serializers.CharField()

class OnboardBanshowserializer(serializers.ModelSerializer):
    class Meta:
        model = OnboardBan
        fields = ['id', 'entryType', 'masteraccount', 'vendor', 'location', 'organization', 'onboardedlines']
    entryType = serializers.CharField()
    masteraccount = serializers.CharField()
    vendor = serializers.CharField()
    location = serializers.CharField()
    organization = serializers.CharField()
    onboardedlines = serializers.StringRelatedField(many=True)


class LocationBANSerializer(serializers.Serializer):
    site_name = serializers.CharField()
    bans = UploadBANSerializer(many=True)

class OrganizationShowOnboardSerializer(serializers.ModelSerializer):
    vendors = serializers.StringRelatedField(many=True)
    locations = serializers.StringRelatedField(many=True)

    class Meta:
        model = Organizations
        fields = ['id', 'Organization_name', 'vendors', 'locations']

from OnBoard.Ban.models import PortalInformation
from View.models import Contracts

class showallSerializer(serializers.ModelSerializer):
    costcenterlevel = serializers.CharField()
    costcentertype = serializers.CharField()
    costcenterstatus = serializers.CharField()
    bantype = serializers.CharField()
    invoicemethod = serializers.CharField()
    paymentType = serializers.CharField()
    portal_info = serializers.SerializerMethodField()
    contract_file = serializers.SerializerMethodField()
    class Meta:
        model = BaseDataTable
        fields = "__all__"

    def get_contract_file(self, obj):
        contractObj = Contracts.objects.filter(
            uploadedban=obj.banUploaded,
            onboardedban=obj.banOnboarded
        ).first()

        if contractObj and contractObj.contract_file:
            return contractObj.contract_file.url  
        return None

    def get_portal_info(self,obj):
        portalObj = PortalInformation.objects.filter(uploadedban=obj.banUploaded, onboardedban=obj.banOnboarded).first()
        return showPortalInfoser(portalObj).data

class BanShowSerializer(serializers.ModelSerializer):
    costcenterlevel = serializers.CharField()
    costcentertype = serializers.CharField()
    costcenterstatus = serializers.CharField()
    bantype = serializers.CharField()
    invoicemethod = serializers.CharField()
    paymentType = serializers.CharField()
    contract_file = serializers.SerializerMethodField()
    active_wireless_count = serializers.SerializerMethodField()
    inactive_wireless_count = serializers.SerializerMethodField()
    total_wireless_count = serializers.SerializerMethodField()
    class Meta:
        model = BaseDataTable
        fields = ['id', 'location', 'accountnumber', 'Entry_type','company','contract_file', 'sub_company', 'vendor', 'created', 'costcenterlevel', 'costcentertype', 'costcenterstatus', 'bantype', 'invoicemethod', 'paymentType','active_wireless_count','inactive_wireless_count','total_wireless_count']

    def get_contract_file(self, obj):
        contractObj = Contracts.objects.filter(
            uploadedban=obj.banUploaded,
            onboardedban=obj.banOnboarded
        ).first()

        if contractObj and contractObj.contract_file:
            return contractObj.contract_file.url  
        return None
    
    def get_total_wireless_count(self,obj):
        return UniquePdfDataTable.objects.filter(banUploaded=obj.banUploaded, banOnboarded=obj.banOnboarded).count()
    def get_active_wireless_count(self,obj):
        return UniquePdfDataTable.objects.filter(banUploaded=obj.banUploaded, banOnboarded=obj.banOnboarded).filter(User_status="Active").count()
    def get_inactive_wireless_count(self,obj):
        return UniquePdfDataTable.objects.filter(banUploaded=obj.banUploaded, banOnboarded=obj.banOnboarded).filter(User_status="Inactive").count()




class CompanyShowOnboardSerializer(serializers.ModelSerializer):
    company_organizations = OrganizationShowOnboardSerializer(many=True, read_only=True)

    class Meta:
        model = Company
        fields = ['id', 'Company_name', 'company_organizations']

class BaseDataTableShowSerializer(serializers.ModelSerializer):
    contract_file = serializers.SerializerMethodField()

    class Meta:
        model = BaseDataTable
        fields = ('company', 'sub_company', 'location','vendor','accountnumber','Entry_type','banUploaded','banOnboarded','contract_file')
    def get_contract_file(self, obj):
        contractObj = Contracts.objects.filter(
            uploadedban=obj.banUploaded,
            onboardedban=obj.banOnboarded
        ).first()

        if contractObj and contractObj.contract_file:
            return contractObj.contract_file.url  
        return None

class BaseDataTableAllShowSerializer(serializers.ModelSerializer):
    contract_file = serializers.SerializerMethodField()
    class Meta:
        model = BaseDataTable
        fields = '__all__'
    def get_contract_file(self, obj):
        contractObj = Contracts.objects.filter(
            uploadedban=obj.banUploaded,
            onboardedban=obj.banOnboarded
        ).first()

        if contractObj and contractObj.contract_file:
            return contractObj.contract_file.url  
        return None
from OnBoard.Ban.models import UniquePdfDataTable
class UniqueTableShowSerializer(serializers.ModelSerializer):
    banOnboarded = serializers.CharField(max_length=255)
    class Meta:
        model = UniquePdfDataTable
        fields = '__all__'
class UniqueTableSaveSerializer(serializers.ModelSerializer):
    class Meta:
        model = UniquePdfDataTable
        fields = '__all__'
class BaselineSaveSerializer(serializers.ModelSerializer):
    class Meta:
        model = BaselineDataTable
        fields = '__all__'
class LineShowSerializer(serializers.ModelSerializer):
    account_number = serializers.CharField(max_length=255)
    class Meta:
        model = Lines
        fields = '__all__'

class BanSaveSerializer(serializers.ModelSerializer):
    class Meta:
        model = BaseDataTable
        fields = '__all__'
