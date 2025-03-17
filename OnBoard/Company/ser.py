from rest_framework import serializers
from .models import Company 
from Dashboard.ModelsByPage.DashAdmin import Vendors
import ast
class CompanyOperationSerializer(serializers.ModelSerializer):
    vendors = serializers.ListField(
        child=serializers.CharField(max_length=255),
        write_only=True,
        required=True
    )
    
    class Meta:
        model = Company
        fields = '__all__'
        

    # validate company_name not already present
    def validate_company_name(self, value):
        if Company.objects.filter(Company_name=value).exists():
            raise serializers.ValidationError(f"Company with name '{value}' already exists.")
        return value

    def create(self, validated_data):
        vendors_data = validated_data.pop('vendors', [])

        print(vendors_data)
        vendors_data = ast.literal_eval(str(vendors_data))
        print(vendors_data)
        company = Company.objects.create(**validated_data)
        if vendors_data:
            vendors = Vendors.objects.filter(name__in=vendors_data)
            company.vendors.set(vendors)
        return company
    
    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value) 
        instance.save()
        return instance


class CompanyShowSerializer(serializers.ModelSerializer):
    vendors = serializers.StringRelatedField(many=True)
    class Meta:
        model = Company
        fields = '__all__'

    def get_vendors(self, obj):
        return [vendor.name for vendor in obj.vendors.all()]