from rest_framework import serializers
from .models import Analysis, MultipleFileUpload
from OnBoard.Company.models import Company
from Dashboard.ModelsByPage.DashAdmin import Vendors
from authenticate.models import PortalUser

class AnalysisSaveSerializer(serializers.ModelSerializer):
    company = serializers.CharField(max_length=255)
    vendor = serializers.CharField(max_length=255)
    created_by = serializers.CharField(max_length=255)

    class Meta:
        model = Analysis
        fields = '__all__'

    def create(self, validated_data):
        companyname = validated_data.pop('company', None)
        company = None
        try:
            company = Company.objects.get(Company_name=companyname)
        except Company.DoesNotExist:
            company = None
        vendorname = validated_data.pop('vendor', None)
        vendor = None
        try:
            vendor = Vendors.objects.get(name=vendorname)
        except Vendors.DoesNotExist:
            raise serializers.ValidationError({"vendor": "Vendor not found"})
        
        username = validated_data.pop('created_by', None)
        user = None
        try:
            user = PortalUser.objects.get(email=username)
        except PortalUser.DoesNotExist:
            raise serializers.ValidationError({"created_by": "User not found"})
        
        validated_data['company'] = company
        validated_data['vendor'] = vendor
        validated_data['created_by'] = user

        analysis = Analysis.objects.create(**validated_data)
        return analysis
    
    def update(self, instance, validated_data):
        companyname = validated_data.pop('company', None)
        company = None
        try:
            company = Company.objects.get(Company_name=companyname)
        except Company.DoesNotExist:
            raise serializers.ValidationError({"company": "Company not found"})
        vendorname = validated_data.pop('vendor', None)
        vendor = None
        try:
            vendor = Vendors.objects.get(name=vendorname)
        except Vendors.DoesNotExist:
            raise serializers.ValidationError({"vendor": "Vendor not found"})
        username = validated_data.pop('created_by', None)
        user = None
        try:
            user = PortalUser.objects.get(email=username)
        except PortalUser.DoesNotExist:
            raise serializers.ValidationError({"created_by": "User not found"})
        
        validated_data['company'] = company
        validated_data['vendor'] = vendor
        validated_data['created_by'] = user

        instance.update(**validated_data)
        return instance
    
class AnalysisShowSerializer(serializers.ModelSerializer):
    company = serializers.CharField(max_length=255)
    vendor = serializers.CharField(max_length=255)
    created_by = serializers.CharField(max_length=255)
    class Meta:
        model = Analysis
        fields = ('id', 'company', 'vendor', 'client', 'remark', 'uploadBill', 'created', 'created_by', 'excel', 'is_processed')

class MultipleAnalysisShowSerializer(serializers.ModelSerializer):
    company = serializers.CharField(max_length=255)
    vendor = serializers.CharField(max_length=255)
    created_by = serializers.CharField(max_length=255)
    class Meta:
        model = MultipleFileUpload
        fields = ('id', 'company', 'vendor', 'client', 'remark', 'file1','file2','file3', 'created', 'created_by', 'excel', 'is_processed', 'savings_pdf')

class VendorsShowSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vendors
        fields = ('name',)

class MultipleAnalysisSerializer(serializers.ModelSerializer):
    company = serializers.CharField(max_length=255)
    vendor = serializers.CharField(max_length=255)
    created_by = serializers.CharField(max_length=255)

    class Meta:
        model = MultipleFileUpload
        fields = '__all__'

    def create(self, validated_data):
        companyname = validated_data.pop('company', None)
        company = None
        try:
            company = Company.objects.get(Company_name=companyname)
        except Company.DoesNotExist:
            company = None
        vendorname = validated_data.pop('vendor', None)
        vendor = None
        try:
            vendor = Vendors.objects.get(name=vendorname)
        except Vendors.DoesNotExist:
            raise serializers.ValidationError({"vendor": "Vendor not found"})
        
        username = validated_data.pop('created_by', None)
        user = None
        try:
            user = PortalUser.objects.get(email=username)
        except PortalUser.DoesNotExist:
            raise serializers.ValidationError({"created_by": "User not found"})
        
        validated_data['company'] = company
        validated_data['vendor'] = vendor
        validated_data['created_by'] = user

        analysis = MultipleFileUpload.objects.create(**validated_data)
        return analysis