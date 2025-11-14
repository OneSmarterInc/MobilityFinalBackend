from rest_framework import serializers
from OnBoard.Organization.models import Organizations
from OnBoard.Ban.models import UploadBAN, BaseDataTable, UniquePdfDataTable, BaselineDataTable
from Dashboard.ModelsByPage.DashAdmin import Vendors, PaymentType
from ..models import ViewUploadBill

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

class viewbillsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ViewUploadBill
        fields = ["id", "is_processed", "month", "year", "ban", "file"]

class basedatahowSerializer(serializers.ModelSerializer):
    banOnboarded = serializers.CharField(max_length=255)
    inventory = serializers.CharField(max_length=255)
    paymentType = serializers.CharField(max_length=255)
    is_bill_in_batch = serializers.SerializerMethodField()
    is_bill_approved = serializers.SerializerMethodField()
    is_bill_payment_done = serializers.SerializerMethodField()
    is_paper_bill = serializers.SerializerMethodField()
    class Meta:
        model = BaseDataTable
        fields = '__all__'
    def get_is_bill_in_batch(self,obj):
        return obj.is_baseline_approved
    def get_is_bill_approved(self,obj):
        return "approved" in obj.batch_approved.lower() if obj.batch_approved else False
    def get_is_bill_payment_done(self,obj):
        return obj.Check.lower() not in ("", None, "null", "false") if obj.Check else False
    def get_is_paper_bill(self,obj):
        return obj.viewpapered is not None
    
    

class uniquepdftableSerializer(serializers.ModelSerializer):
    banOnboarded = serializers.CharField(max_length=255)
    inventory = serializers.CharField(max_length=255)
    class Meta:
        model = UniquePdfDataTable
        fields = ('id', 'inventory', 'banOnboarded', 'account_number','user_name', 'total_charges', 'wireless_number')

from collections import defaultdict
import json
class BaselinedataSerializer(serializers.ModelSerializer):
    onboarded_categories = serializers.CharField(read_only=True)
    category_object = serializers.CharField(read_only=True)

    class Meta:
        model = BaselineDataTable
        fields = '__all__'

    def to_representation(self, instance):
        rep = super().to_representation(instance)

        wireless_to_categories = self.context.get('wireless_to_categories')
        if not wireless_to_categories:
            onboarded_objects = self.context.get('onboarded_objects', [])
            wireless_to_categories = defaultdict(list)
            for obj in onboarded_objects:
                val = obj.category_object
                # val = add_tag_to_dict(val)
                if isinstance(val, dict):
                    import json
                    val = json.dumps(val)
                wireless_to_categories[obj.Wireless_number].append(val)
            self.context['wireless_to_categories'] = wireless_to_categories

        categories_list = wireless_to_categories.get(instance.Wireless_number, [])
        rep['onboarded_categories'] = categories_list[0] if categories_list else ""

        if not isinstance(rep.get('category_object'), str):
            import json
            rep['category_object'] = json.dumps(rep.get('category_object', {}))

        return rep

    
class BaselineDataTableShowSerializer(serializers.ModelSerializer):
    class Meta:
        model = BaselineDataTable
        fields = '__all__'
        
class showaccountbasetable(serializers.ModelSerializer):
    class Meta:
        model = BaseDataTable
        fields = ('accountnumber', 'vendor', 'sub_company')

class showbaselinenotesSerializer(serializers.ModelSerializer):
    variance = serializers.SerializerMethodField()
    class Meta:
        model = BaseDataTable
        fields = ('id','baseline_notes', 'variance', 'is_baseline_approved', 'is_baseline_replaced')
    def get_variance(self, obj):
        mainObj = BaseDataTable.objects.exclude(banOnboarded=None, banUploaded=None).filter(sub_company=obj.sub_company, vendor=obj.vendor, accountnumber=obj.accountnumber).first()
        return mainObj.variance if mainObj else 5

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

def add_tag_to_dict(baseline):
    formatted = json.loads(baseline) if isinstance(baseline, str) else baseline
    for key, value in formatted.items():
        if isinstance(value, dict):
            for sub_key, sub_value in value.items():
                if not isinstance(sub_value, dict):
                    value[sub_key] = f"{sub_value} - True"
        else:
            formatted[key] = f"{value} - True"
    return formatted