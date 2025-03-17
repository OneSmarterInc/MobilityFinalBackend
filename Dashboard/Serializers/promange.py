from rest_framework import serializers
from OnBoard.Ban.models import UniquePdfDataTable
from OnBoard.Organization.models import Organizations
class OrganizationsShowSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organizations
        fields = ['id', 'Organization_name',]