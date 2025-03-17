from rest_framework import serializers
from OnBoard.Organization.models import Organizations
from OnBoard.Ban.models import UploadBAN, BaseDataTable, UniquePdfDataTable
from Dashboard.ModelsByPage.DashAdmin import Vendors, PaymentType

class showBanSerializer(serializers.ModelSerializer):
    organization = serializers.CharField(max_length=255)
    Vendor = serializers.CharField(max_length=255)
    class Meta:
        model = UploadBAN
        fields = ['account_number','organization', 'Vendor']

class showOrganizationSerializer(serializers.ModelSerializer):
    vendors = serializers.StringRelatedField(many=True)
    class Meta:
        model = Organizations
        fields = ['Organization_name', 'vendors','bans']

class vendorshowSerializer(serializers.ModelSerializer):
    name = serializers.CharField(max_length=255)
    class Meta:
        model = Vendors
        fields = ['name',]


class paytypehowSerializer(serializers.ModelSerializer):
    name = serializers.CharField(max_length=255)
    class Meta:
        model = PaymentType
        fields = ['name',]

class basedatahowSerializer(serializers.ModelSerializer):
    banOnboarded = serializers.CharField(max_length=255)
    inventory = serializers.CharField(max_length=255)
    paymentType = serializers.CharField(max_length=255)
    class Meta:
        model = BaseDataTable
        fields = '__all__'

class uniquepdftableSerializer(serializers.ModelSerializer):
    banOnboarded = serializers.CharField(max_length=255)
    inventory = serializers.CharField(max_length=255)
    class Meta:
        model = UniquePdfDataTable
        fields = ('id', 'inventory', 'banOnboarded', 'account_number','user_name', 'total_charges', 'wireless_number')