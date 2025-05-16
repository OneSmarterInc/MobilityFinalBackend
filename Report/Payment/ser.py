from rest_framework import serializers
from OnBoard.Ban.models import BaseDataTable, UniquePdfDataTable, BaselineDataTable
from OnBoard.Organization.models import Organizations
from OnBoard.Company.models import Company

from collections import defaultdict
class baselinedataserializer(serializers.ModelSerializer):
    class Meta:
        model = BaselineDataTable
        fields = ['account_number', 'company', 'vendor','sub_company','total_charges','Wireless_number','paymentstatus']



class OrganizationShowOnboardSerializer(serializers.ModelSerializer):
    vendors = serializers.StringRelatedField(many=True)

    class Meta:
        model = Organizations
        fields = ['id', 'Organization_name', 'vendors']

class CompanyShowOnboardSerializer(serializers.ModelSerializer):
    company_organizations = OrganizationShowOnboardSerializer(many=True, read_only=True)

    class Meta:
        model = Company
        fields = ['id', 'Company_name', 'company_organizations']

class BaseDataTableShowSerializer(serializers.ModelSerializer):
    class Meta:
        model = BaseDataTable
        fields = ['company', 'sub_company','vendor','accountnumber']