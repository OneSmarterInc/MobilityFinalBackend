from rest_framework import serializers
from OnBoard.Organization.models import Organizations
from OnBoard.Ban.models import UploadBAN, BaseDataTable, UniquePdfDataTable, BaselineDataTable
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

from collections import defaultdict
class BaselinedataSerializer(serializers.ModelSerializer):
    onboarded_categories = serializers.SerializerMethodField()

    class Meta:
        model = BaselineDataTable
        fields = '__all__'
        extra_fields = ['onboarded_categories']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Prepare the mapping once during serializer initialization
        onboarded_objects = self.context.get('onboarded_objects')
        wireless_to_categories = defaultdict(list)
        for obj in onboarded_objects:
            wireless_to_categories[obj.Wireless_number].append(obj.category_object)
        
        # Save it in context for use in get_onboarded_categories
        self.context['wireless_to_categories'] = wireless_to_categories

    def get_onboarded_categories(self, obj):
        wireless_to_categories = self.context.get('wireless_to_categories', {})
        return wireless_to_categories.get(obj.Wireless_number)
    
class BaselineDataTableShowSerializer(serializers.ModelSerializer):
    class Meta:
        model = BaselineDataTable
        fields = '__all__'
        
class showaccountbasetable(serializers.ModelSerializer):
    class Meta:
        model = BaseDataTable
        fields = ('accountnumber', 'vendor', 'sub_company')

class BaselineWithOnboardedCategorySerializer(serializers.ModelSerializer):
    onboarded_category = serializers.SerializerMethodField()
    class Meta:
        model = BaselineDataTable
        fields = [
            'id',
            'account_number',
            'Wireless_number',
            'viewuploaded',
            'banOnboarded',
            'category_object',
            'onboarded_category'
        ]

    def get_onboarded_category(self, obj):
        if obj.viewuploaded is None:
            return None
        
        related = BaselineDataTable.objects.filter(
            account_number=obj.account_number,
            Wireless_number=obj.Wireless_number
        ).first()
        return related.category_object if related else None