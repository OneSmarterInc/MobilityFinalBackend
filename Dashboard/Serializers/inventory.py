from rest_framework import serializers

from OnBoard.Ban.models import UniquePdfDataTable, BaselineDataTable, BaseDataTable
from OnBoard.Organization.models import Organizations
from Dashboard.ModelsByPage.DashAdmin import Vendors

class UniqueTableShowSerializer(serializers.ModelSerializer):
    banOnboarded = serializers.CharField(max_length=255)
    class Meta:
        model = UniquePdfDataTable
        fields = '__all__' 

class BaselineTableShowSerializer(serializers.ModelSerializer):
    banOnboarded = serializers.CharField(max_length=255)
    class Meta:
        model = BaselineDataTable
        fields = '__all__'
         
class OrganizationsShowSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organizations
        fields = '__all__'

class showBaseDataser(serializers.ModelSerializer):
    class Meta:
        model = BaseDataTable
        fields = ('accountnumber', 'sub_company', 'vendor')

class VendorsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vendors
        fields = ('name',)