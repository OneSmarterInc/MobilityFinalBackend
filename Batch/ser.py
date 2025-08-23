from rest_framework import serializers
from OnBoard.Ban.models import BatchReport, BaseDataTable
from OnBoard.Organization.models import Organizations

class BatchReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = BatchReport
        fields = '__all__'
    
class OrganizationShowSerializer(serializers.ModelSerializer):

    class Meta:
        model = Organizations
        fields = ['id', 'Organization_name']

class BaseDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = BaseDataTable
        fields = '__all__'