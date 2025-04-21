from rest_framework import serializers
from .models import Company 
from Dashboard.ModelsByPage.DashAdmin import Vendors
import ast
class CompanyOperationSerializer(serializers.ModelSerializer):

    class Meta:
        model = Company
        fields = '__all__'
        

    # validate company_name not already present
    def validate_company_name(self, value):
        if Company.objects.filter(Company_name=value).exists():
            raise serializers.ValidationError(f"Company with name already exists.")
        return value

    def create(self, validated_data):
  
        company = Company.objects.create(**validated_data)

        return company
    
    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value) 
        instance.save()
        return instance


class CompanyShowSerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = '__all__'