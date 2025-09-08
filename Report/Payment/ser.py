from rest_framework import serializers
from OnBoard.Ban.models import BaseDataTable, UniquePdfDataTable, BaselineDataTable
from OnBoard.Organization.models import Organizations
from OnBoard.Company.models import Company

from collections import defaultdict
class baselinedataserializer(serializers.ModelSerializer):
    due_date = serializers.SerializerMethodField()
    class Meta:
        model = BaselineDataTable
        fields = ['account_number', 'company', 'vendor','sub_company','total_charges','Wireless_number','paymentstatus','due_date']

    def get_due_date(self, obj):
        baseObj = BaseDataTable.objects.filter(banOnboarded=obj.banOnboarded, banUploaded=obj.banUploaded).first()
        return baseObj.date_due if baseObj else None

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