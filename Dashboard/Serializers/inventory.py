from rest_framework import serializers

from OnBoard.Ban.models import UniquePdfDataTable
from OnBoard.Organization.models import Organizations

class UniqueTableShowSerializer(serializers.ModelSerializer):
    banOnboarded = serializers.CharField(max_length=255)
    class Meta:
        model = UniquePdfDataTable
        fields = '__all__' 

class OrganizationsShowSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organizations
        fields = '__all__'