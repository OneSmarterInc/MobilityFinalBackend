

from rest_framework import serializers
from .models import UploadBAN, OnboardBan, InventoryUpload, Lines
from Dashboard.ModelsByPage.DashAdmin import Vendors, EntryType, BanStatus, BanType, InvoiceMethod, PaymentType, CostCenterLevel, CostCenterType, BillType
from ..Organization.models import Organizations
from..Company.models import Company
from..Location.models import Location
from authenticate.models import PortalUser


class LinesSerializer(serializers.ModelSerializer):
    account_number = serializers.PrimaryKeyRelatedField(queryset=UploadBAN.objects.all())

    class Meta:
        model = Lines
        fields = '__all__'

class UploadBANSerializer(serializers.ModelSerializer):
    lines = LinesSerializer(many=True, required=False)
    user_email = serializers.CharField()
    Vendor = serializers.CharField()
    company = serializers.CharField()
    organization = serializers.CharField()
    entryType = serializers.CharField()
    location = serializers.CharField()
    banstatus = serializers.CharField()
    bantype = serializers.CharField()
    invoicemethod = serializers.CharField()
    paymenttype = serializers.CharField()
    costcenterlevel = serializers.CharField()
    costcentertype = serializers.CharField()

    class Meta:
        model = UploadBAN
        fields = '__all__'

    def create(self, validated_data):
        lines_data = validated_data.pop('lines', [])

        company_name = validated_data.pop('company')
        organization_name = validated_data.pop('organization')
        user_email = validated_data.pop('user_email')
        vendor_name = validated_data.pop('Vendor')
        entrytype_name = validated_data.pop('entryType')
        loc_name = validated_data.pop('location')
        banstatus_name = validated_data.pop('banstatus')
        bantype_name = validated_data.pop('bantype')
        invoicemethod_name = validated_data.pop('invoicemethod')
        paymenttype_name = validated_data.pop('paymenttype')


        try:
            company = Company.objects.get(Company_name=company_name)
            organization = Organizations.objects.get(Organization_name=organization_name)
        except Company.DoesNotExist:
            raise serializers.ValidationError({"company": "Company not found"})
        except Organizations.DoesNotExist:
            raise serializers.ValidationError({"organization": "Organization not found"})
        try: 
            user = PortalUser.objects.get(email=user_email)
        except PortalUser.DoesNotExist:
            raise serializers.ValidationError({"user_email": "User not found"})
        try:
            vendor = Vendors.objects.get(name=vendor_name)
            entrytype = EntryType.objects.get(name=entrytype_name)
            location = Location.objects.get(site_name=loc_name)
            banstatus = BanStatus.objects.get(name=banstatus_name)
            bantype = BanType.objects.get(name=bantype_name)
            paymenttype = PaymentType.objects.get(name=paymenttype_name)
            invoicemethod = InvoiceMethod.objects.get(name=invoicemethod_name)
        except Vendors.DoesNotExist:
            raise serializers.ValidationError({"vendor": "Vendor not found"})
        except EntryType.DoesNotExist:
            raise serializers.ValidationError({"entryType": "Entry Type not found"})
        except Location.DoesNotExist:
            raise serializers.ValidationError({"location": "Location not found"})
        except BanStatus.DoesNotExist:
            raise serializers.ValidationError({"banstatus": "Ban Status not found"})
        except InvoiceMethod.DoesNotExist:
            raise serializers.ValidationError({"invoicemethod": "Invoice Method not found"})
        except BanType.DoesNotExist:
            raise serializers.ValidationError({"bantype": "Ban Type not found"})
        except PaymentType.DoesNotExist:
            raise serializers.ValidationError({"paymenttype": "Payment Type not found"})
        
        try:
            costcenterlvlname = validated_data.pop('cost_center_level')
            costcentertypname = validated_data.pop('cost_center_type')
            print(costcentertypname, costcenterlvlname)
            costcenterlevelobj = CostCenterLevel.objects.get(name=costcenterlvlname)
            costcentertypeobj = CostCenterType.objects.get(name=costcentertypname)
            print(costcentertypeobj, costcenterlevelobj)
        except CostCenterLevel.DoesNotExist:
            raise serializers.ValidationError({"cost_center_level": "Cost Center Level not found"})
        except CostCenterType.DoesNotExist:
            raise serializers.ValidationError({"cost_center_type": "Cost Center Type not found"})
        
        upload_ban = UploadBAN.objects.create(
            user_email=user,
            Vendor=vendor,
            company=company, 
            organization=organization, 
            entryType=entrytype, 
            location=location, 
            costcenterlevel=costcenterlevelobj, 
            costcentertype=costcentertypeobj, 
            banstatus=banstatus, 
            bantype=bantype, 
            paymenttype=paymenttype,
            invoicemethod=invoicemethod, 
            **validated_data
        )

        for line_data in lines_data:
            print(line_data)
            Lines.objects.create(account_number=upload_ban, **line_data)

        return upload_ban

    def update(self, instance, validated_data):
        lines_data = validated_data.pop('lines', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if lines_data is not None:
            instance.lines.all().delete()
            for line_data in lines_data:
                Lines.objects.create(account_number=instance, **line_data)

        return instance
    


class OnboardBanSerializer(serializers.ModelSerializer):
    organization = serializers.PrimaryKeyRelatedField(
        queryset=Organizations.objects.all(), allow_null=True)
    vendor = serializers.PrimaryKeyRelatedField(
        queryset=Vendors.objects.all(), allow_null=True)
    entryType = serializers.PrimaryKeyRelatedField(
        queryset=EntryType.objects.all(), allow_null=True)
    masteraccount = serializers.PrimaryKeyRelatedField(
        queryset=EntryType.objects.all(), allow_null=True)
    location = serializers.PrimaryKeyRelatedField(
        queryset=Location.objects.all(), allow_null=True)
    uploadBill = serializers.FileField(required=True)

    class Meta:
        model = OnboardBan
        fields = '__all__'

    def create(self, validated_data):
        return OnboardBan.objects.create(**validated_data)

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance
    

class InventoryUploadSerializer(serializers.ModelSerializer):
    organization = serializers.PrimaryKeyRelatedField(
        queryset=Organizations.objects.all()
    )
    vendor = serializers.PrimaryKeyRelatedField(
        queryset=Vendors.objects.all(), allow_null=True
    )
    ban = serializers.PrimaryKeyRelatedField(
        queryset=UploadBAN.objects.all()
    )

    class Meta:
        model = InventoryUpload
        fields = ['id', 'organization', 'vendor', 'ban', 'uploadFile', 'created', 'updated']
        read_only_fields = ['created', 'updated']

    def create(self, validated_data):
        return InventoryUpload.objects.create(**validated_data)

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance
    

class OrganizationShowOnboardSerializer(serializers.ModelSerializer):
    vendors = serializers.StringRelatedField(many=True)
    locations = serializers.StringRelatedField(many=True)
    bans = serializers.SerializerMethodField()
    company = serializers.CharField(max_length=255, read_only=True)

    class Meta:
        model = Organizations
        fields = ['id', 'Organization_name', 'vendors', 'locations', 'bans', 'company']


    def get_vendors(self, obj):
        return [vendor.name for vendor in obj.vendors.all()]
    
    def get_locations(self, obj):
        return [location.site_name for location in obj.locations.all()]
    
    def get_bans(self, obj):
        return [ban.account_number for ban in UploadBAN.objects.filter(organization=obj)]
    
    def get_company(self, obj):
        return obj.company.Company_name

class EntryTypeShowSerializer(serializers.ModelSerializer):
    class Meta:
        model = EntryType
        fields = ['name', ]

class BillTypeShowSerializer(serializers.ModelSerializer):
    class Meta:
        model = BillType
        fields = ['name', ]