from rest_framework import serializers
from .models import Organizations, Division, Links
from Dashboard.ModelsByPage.DashAdmin import Vendors
from ..Company.models import Company
from ..Location.models import Location
import ast

class OrganizationSaveSerializer(serializers.ModelSerializer):
    vendors = serializers.ListField(
        child=serializers.CharField(max_length=255),
        write_only=True,
        required=False  
    )
    company = serializers.CharField(max_length=255, write_only=True, required=True)

    class Meta:
        model = Organizations
        fields = '__all__'
        read_only_fields = ['created', 'updated', 'company', 'organization_name']

    def validate_company(self, value):
        if not Company.objects.filter(Company_name=value).exists():
            raise serializers.ValidationError(f"Company with name '{value}' does not exist.")
        return value

    def create(self, validated_data):
        company_name = validated_data.pop('company')
        try:
            company = Company.objects.get(Company_name=company_name)
        except Company.DoesNotExist:
            raise serializers.ValidationError({"company": f"Company with name '{company_name}' does not exist."})

        # Extract vendors data
        vendors_data = validated_data.pop('vendors', [])
        vendors_data = str(vendors_data).removeprefix("['").removesuffix("']").split(",")
        organization = Organizations.objects.create(**validated_data, company=company)

        if vendors_data:
            vendors = Vendors.objects.filter(name__in=vendors_data)
            organization.vendors.set(vendors)

        return organization
    
    def update(self, instance, validated_data):
        validated_data.pop('company', None)
        validated_data.pop('organization_name', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance





class OrganizationShowSerializer(serializers.ModelSerializer):
    vendors = serializers.StringRelatedField(many=True)
    locations = serializers.StringRelatedField(many=True)
    company = serializers.CharField(max_length=255, read_only=True)
    links = serializers.StringRelatedField(many=True)
    divisions = serializers.StringRelatedField(many=True)

    class Meta:
        model = Organizations
        fields = '__all__'


    def get_vendors(self, obj):
        return [vendor.name for vendor in obj.vendors.all()]
    
    def get_locations(self, obj):
        return [location.site_name for location in obj.locations.all()]
    
    def get_company(self, obj):
        return obj.company.Company_name
    
    def get_links(self, obj):
        return [link.name for link in obj.links.all()]
    
    def get_divisions(self, obj):
        return [division.name for division in obj.divisions.all()]
    
class CompanyShowSerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = ['Company_name',]

class DivisionSerializer(serializers.ModelSerializer):
    company = serializers.CharField()
    organization = serializers.CharField()

    class Meta:
        model = Division
        fields = '__all__'

    def create(self, validated_data):
        company_name = validated_data.pop('company')
        organization_name = validated_data.pop('organization')

        try:
            company = Company.objects.get(Company_name=company_name)
            organization = Organizations.objects.get(Organization_name=organization_name)
        except Company.DoesNotExist:
            raise serializers.ValidationError({"company": "Company not found"})
        except Organizations.DoesNotExist:
            raise serializers.ValidationError({"organization": "Organization not found"})

        return Division.objects.create(company=company, organization=organization, **validated_data)
    
    def update(self, instance, validated_data):
        if 'company' in validated_data:
            company_name = validated_data.pop('company')
            try:
                company = Company.objects.get(Company_name=company_name)
                instance.company = company
            except Company.DoesNotExist:
                raise serializers.ValidationError({"company": "Company not found"})

        if 'organization' in validated_data:
            organization_name = validated_data.pop('organization')
            try:
                organization = Organizations.objects.get(Organization_name=organization_name)
                instance.organization = organization
            except Organizations.DoesNotExist:
                raise serializers.ValidationError({"organization": "Organization not found"})

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance


    


class LinkSerializer(serializers.ModelSerializer):
    company = serializers.CharField()
    organization = serializers.CharField()

    class Meta:
        model = Links
        fields = '__all__'

    def create(self, validated_data):
        company_name = validated_data.pop('company')
        organization_name = validated_data.pop('organization')

        try:
            company = Company.objects.get(Company_name=company_name)
            organization = Organizations.objects.get(Organization_name=organization_name)
        except Company.DoesNotExist:
            raise serializers.ValidationError({"company": "Company not found"})
        except Organizations.DoesNotExist:
            raise serializers.ValidationError({"organization": "Organization not found"})

        return Links.objects.create(company=company, organization=organization, **validated_data)
    
    def update(self, instance, validated_data):
        if 'company' in validated_data:
            company_name = validated_data.pop('company')
            try:
                company = Company.objects.get(Company_name=company_name)
                instance.company = company
            except Company.DoesNotExist:
                raise serializers.ValidationError({"company": "Company not found"})

        if 'organization' in validated_data:
            organization_name = validated_data.pop('organization')
            try:
                organization = Organizations.objects.get(Organization_name=organization_name)
                instance.organization = organization
            except Organizations.DoesNotExist:
                raise serializers.ValidationError({"organization": "Organization not found"})

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance
    

class DivisionNameSerializer(serializers.ModelSerializer):
    name = serializers.CharField(max_length=255)
    class Meta:
        model = Division
        fields = ('name',)
    
