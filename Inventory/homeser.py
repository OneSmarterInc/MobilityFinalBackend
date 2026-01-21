from rest_framework import serializers
from OnBoard.Company.models import Company
from OnBoard.Organization.models import Organizations
from OnBoard.Location.models import Location
from Dashboard.ModelsByPage.DashAdmin import Vendors, EntryType
from OnBoard.Ban.models import UploadBAN, OnboardBan, BaseDataTable, Lines, UniquePdfDataTable, BaselineDataTable
from Batch.models import EmailConfiguration

class showCompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = ("Company_name",)
    
class showOrganizationSerializer(serializers.ModelSerializer):
    is_email_configured = serializers.SerializerMethodField()
    company = serializers.CharField() 
    locations = serializers.SerializerMethodField()
    vendors = serializers.SerializerMethodField()
    class Meta:
        model = Organizations
        fields = ("id","Organization_name","company","locations","vendors","is_email_configured")
    def get_locations(self,obj):
        locs = Location.objects.filter(organization=obj)
        return [{"id":loc.id, "name":loc.site_name} for loc in locs]
    def get_vendors(self,obj):
        vendors = obj.vendors.all()
        return [{"id":vendor.id, "name":vendor.name} for vendor in vendors]
    def get_is_email_configured(self,obj):
        return EmailConfiguration.objects.filter(sub_company=obj).first() is not None
    

class showOnboardedSerializer(serializers.ModelSerializer):
    company = serializers.SerializerMethodField()
    vendor = serializers.SerializerMethodField()
    organization = serializers.SerializerMethodField()
    entryType = serializers.SerializerMethodField()
    location = serializers.SerializerMethodField()
    no_of_lines = serializers.SerializerMethodField()
    class Meta:
        model = OnboardBan
        fields = ("id", "organization","vendor","entryType","is_processed","location","account_number","company","no_of_lines","created")
    def get_company(self,obj):
        return obj.organization.company.Company_name
    def get_organization(self,obj):
        return {"name":obj.organization.Organization_name, "id":obj.organization.id} if obj.organization else None
    def get_entryType(self,obj):
        return {"name":obj.entryType.name, "id":obj.entryType.id} if obj.entryType else None
    def get_location(self,obj):
        return {"name":obj.location.site_name, "id":obj.location.id} if obj.location else {"name":"","id":""}
    def get_vendor(self,obj):
        return {"name":obj.vendor.name, "id":obj.vendor.id} if obj.vendor else None
    def get_no_of_lines(self,obj):
        return len(UniquePdfDataTable.objects.filter(banOnboarded=obj.id))
    
class showUploadedSerializer(serializers.ModelSerializer):
    company = serializers.SerializerMethodField()
    vendor = serializers.SerializerMethodField()
    organization = serializers.SerializerMethodField()
    entryType = serializers.SerializerMethodField()
    location = serializers.SerializerMethodField()
    no_of_lines = serializers.SerializerMethodField()
    is_processed = serializers.SerializerMethodField()
    class Meta:
        model = UploadBAN
        fields = ("id", "organization","vendor","entryType","location","account_number","no_of_lines","company","is_processed","created")

    def get_company(self,obj):
        return obj.organization.company.Company_name if obj.organization else None
    def get_organization(self,obj):
        return {"name":obj.organization.Organization_name, "id":obj.organization.id} if obj.organization else None
    def get_entryType(self,obj):
        return {"name":obj.entryType.name, "id":obj.entryType.id} if obj.entryType else None
    def get_location(self,obj):
        return {"name":obj.location.site_name, "id":obj.location.id} if obj.location else {"name":"","id":""}
    def get_vendor(self,obj):
        return {"name":obj.Vendor.name, "id":obj.Vendor.id} if obj.Vendor else None
    def get_no_of_lines(self,obj):
        return len(UniquePdfDataTable.objects.filter(banUploaded=obj.id))
    def get_is_processed(self,obj):
        return True
