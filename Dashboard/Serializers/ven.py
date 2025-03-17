from rest_framework import serializers
from ..ModelsByPage.DashAdmin import Vendors
from OnBoard.Organization.models import Organizations


class OrganizationListSerializer(serializers.ModelSerializer):
    vendors = serializers.StringRelatedField(many=True)
    favorite_vendors = serializers.StringRelatedField(many=True)
    class Meta:
        model = Organizations
        fields = ['id', 'Organization_name', 'vendors', 'favorite_vendors']


class VendorsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vendors
        fields = "__all__"