from rest_framework import serializers
from OnBoard.Company.models import Company
from OnBoard.Organization.models import Organizations
from OnBoard.Location.models import Location
from Dashboard.ModelsByPage.DashAdmin import Vendors, EntryType
from OnBoard.Ban.models import UploadBAN, OnboardBan, BaseDataTable, Lines, UniquePdfDataTable

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

class OrganizationGetAllDataSerializer(serializers.ModelSerializer):
    vendors = VendorNameSerializer(many=True)
    company = CompanygetNameSerializer()
    divisions = serializers.StringRelatedField(many=True)
    class Meta:
        model = Organizations
        fields = '__all__'

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

class BanShowSerializer(serializers.ModelSerializer):
    class Meta:
        model = UploadBAN
        fields = ['id', 'location', 'account_number', 'entryType','company', 'organization', 'Vendor', 'uploadedlines', 'created']

    entryType = serializers.CharField()
    uploadedlines = serializers.StringRelatedField(many=True)
    location = serializers.CharField()
    company = serializers.CharField()
    organization = serializers.CharField()
    Vendor = serializers.CharField()
    

    def get_bans(self, obj):
        grouped_bans = defaultdict(list)
        for ban in obj.bans.all():
            location_name = ban.location.site_name if ban.location else "Unknown"
            grouped_bans[location_name].append(UploadBANSerializer(ban).data)

        return [{'site_name': location, 'bans': bans} for location, bans in grouped_bans.items()]


class CompanyShowOnboardSerializer(serializers.ModelSerializer):
    company_organizations = OrganizationShowOnboardSerializer(many=True, read_only=True)

    class Meta:
        model = Company
        fields = ['id', 'Company_name', 'company_organizations']

class BaseDataTableShowSerializer(serializers.ModelSerializer):
    banOnboarded = serializers.CharField(max_length=255)
    class Meta:
        model = BaseDataTable
        fields = '__all__'

from OnBoard.Ban.models import UniquePdfDataTable
class UniqueTableShowSerializer(serializers.ModelSerializer):
    banOnboarded = serializers.CharField(max_length=255)
    class Meta:
        model = UniquePdfDataTable
        fields = '__all__'

class LineShowSerializer(serializers.ModelSerializer):
    account_number = serializers.CharField(max_length=255)
    class Meta:
        model = Lines
        fields = '__all__'
