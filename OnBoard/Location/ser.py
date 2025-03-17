from .models import Location
from rest_framework import serializers
from ..Organization.models import Organizations, Division
from ..Company.models import Company


class LocationSerializer(serializers.ModelSerializer):
    company = serializers.CharField()
    organization = serializers.CharField()
    division = serializers.CharField()
    class Meta:
        model = Location
        fields = '__all__'

    def create(self, validated_data):
        print(validated_data)
        company_name = validated_data.pop('company')
        organization_name = validated_data.pop('organization')
        division_name = validated_data.pop('division')
        print(company_name, organization_name, division_name)
        try:
            company = Company.objects.get(Company_name=company_name)
            organization = Organizations.objects.get(Organization_name=organization_name)
            division = Division.objects.get(organization=organization, name=division_name)
        except Company.DoesNotExist:
            raise serializers.ValidationError({"company": "Company not found"})
        except Organizations.DoesNotExist:
            raise serializers.ValidationError({"organization": "Organization not found"})
        except Division.DoesNotExist:
            raise serializers.ValidationError({"division": "Division already exists"})

        return Location.objects.create(company=company, organization=organization, division=division, **validated_data)
    
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
    
class LocationSaveSerializer(serializers.ModelSerializer):
    company = serializers.PrimaryKeyRelatedField(queryset=Company.objects.all(), allow_null=True, required=False)
    organization = serializers.PrimaryKeyRelatedField(queryset=Organizations.objects.all())
    division = serializers.PrimaryKeyRelatedField(queryset=Division.objects.all(), allow_null=True, required=False)

    class Meta:
        model = Location
        fields = '__all__'
    

class LocationShowSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = "__all__"
    