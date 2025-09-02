from rest_framework import serializers
from OnBoard.Organization.models import Organizations
from OnBoard.Company.models import Company
from Dashboard.ModelsByPage.DashAdmin import Vendors
from OnBoard.Ban.models import UploadBAN, BaseDataTable, UniquePdfDataTable, BaselineDataTable
from .models import Report_Unbilled_Data, Report_Billed_Data

class OrganizationShowSerializer(serializers.ModelSerializer):
    vendors = serializers.StringRelatedField(many=True)
    locations = serializers.StringRelatedField(many=True)
    company = serializers.CharField()

    class Meta:
        model = Organizations
        fields = ['id', 'Organization_name', 'vendors', 'locations','company']


class VendorShowSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vendors
        fields = ['name',]
    
class showBanSerializer(serializers.ModelSerializer):
    class Meta:
        model = BaseDataTable
        fields = ['accountnumber','sub_company', 'vendor']

class saveUnbilledSerializer(serializers.ModelSerializer):
    class Meta:
        model = Report_Unbilled_Data
        fields = '__all__'
    def create(self, validated_data):
        validated_data.pop('report_type', None)
        org = validated_data['sub_company']
        orgobj = Organizations.objects.filter(Organization_name=org)[0]
        vendor = validated_data['vendor']
        vendorobj = Vendors.objects.filter(name=vendor)[0]
        companyobj = Company.objects.filter(Company_name=orgobj.company.Company_name)[0]


        validated_data['company'] = companyobj
        validated_data['organization'] = orgobj
        validated_data['vendor'] = vendorobj

        return Report_Unbilled_Data.objects.create(**validated_data)

class saveBilledSerializer(serializers.ModelSerializer):
    vendor = serializers.CharField()
    organization = serializers.CharField()
    company = serializers.CharField()
    class Meta:
        model = Report_Billed_Data
        fields = '__all__'
    def create(self, validated_data):
        validated_data['Report_Type'] = validated_data.pop('report_type', None)

        # Ensure organization is correctly retrieved
        org_name = validated_data.pop('sub_company', None)  # Fix this line
        if not org_name:
            raise serializers.ValidationError({"sub_company": "This field is required."})
        
        try:
            orgobj = Organizations.objects.get(Organization_name=org_name)
        except Organizations.DoesNotExist:
            raise serializers.ValidationError({"organization": f"Organization '{org_name}' not found."})

        # Ensure vendor is correctly retrieved
        vendor_name = validated_data.pop('vendor', None)
        if not vendor_name:
            raise serializers.ValidationError({"vendor": "This field is required."})
        
        try:
            vendorobj = Vendors.objects.get(name=vendor_name)
        except Vendors.DoesNotExist:
            raise serializers.ValidationError({"vendor": f"Vendor '{vendor_name}' not found."})

        # Ensure company is correctly retrieved
        try:
            companyobj = Company.objects.get(Company_name=orgobj.company.Company_name)
        except Company.DoesNotExist:
            raise serializers.ValidationError({"company": f"Company '{orgobj.company.Company_name}' not found."})

        validated_data['File'] = validated_data.pop('file', None)
        validated_data['Account_Number'] = validated_data.pop('account_number', None)

        print("Final Validated Data:", validated_data)

        return Report_Billed_Data.objects.create(
            company=companyobj, organization=orgobj, vendor=vendorobj, **validated_data
        )

    
    def update(self, instance, validated_data):
        validated_data['Report_Type'] = validated_data.pop('report_type', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

class showBilledReport(serializers.ModelSerializer):
    company = serializers.CharField()
    organization = serializers.CharField()
    vendor = serializers.CharField()

    class Meta:
        model = Report_Billed_Data
        fields = '__all__'

class showUnbilledReport(serializers.ModelSerializer):
    company = serializers.CharField()
    organization = serializers.CharField()
    vendor = serializers.CharField()
    class Meta:
        model = Report_Unbilled_Data
        fields = '__all__'
