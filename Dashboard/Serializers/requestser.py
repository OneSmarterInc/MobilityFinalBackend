from rest_framework import serializers
from ..ModelsByPage.Req import Requests,Device,MakeModel, VendorDevice, VendorInformation, CostCenters, VendorPlan, TrackingInfo
from OnBoard.Organization.models import Organizations
from authenticate.models import PortalUser
from Dashboard.ModelsByPage.DashAdmin import Vendors
from OnBoard.Ban.models import BaseDataTable, UniquePdfDataTable, BaselineDataTable
from Dashboard.ModelsByPage.ProfileManage import Profile

class devicesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Device
        exclude = ('created','updated')


class showdevicesSerializer(serializers.ModelSerializer):
    model = serializers.SerializerMethodField()
    class Meta:
        model = Device
        exclude = ('created','updated','sub_company')
    def get_model(self, obj):
        return {
            'id': obj.model.id,
            'name': obj.model.name,
            'os': obj.model.os,
        }

class MakeModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = MakeModel
        exclude = ('created','updated')


class showMakeModelSerializer(serializers.ModelSerializer):
    amount = serializers.SerializerMethodField()
    class Meta:
        model = MakeModel
        exclude = ('created','updated','sub_company')
    def get_amount(self,obj):
        device = Device.objects.filter(model=obj.id).first()
        return device.amount if device else 0

class VendorDeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = VendorDevice
        exclude = ('created','updated')


class showVendorDeviceSerializer(serializers.ModelSerializer):
    model = serializers.SerializerMethodField()
    vendor = serializers.SerializerMethodField()
    class Meta:
        model = VendorDevice
        exclude = ('created','updated','sub_company')
    def get_model(self, obj):
        return {
            'id': obj.model.id,
            'name': obj.model.name,
        }
    def get_vendor(self, obj):
        return {
            'id': obj.vendor.id,
            'name': obj.vendor.name,
        }

class VendorInformationSerializer(serializers.ModelSerializer):
    class Meta:
        model = VendorInformation
        exclude = ('created','updated')

class VendorPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = VendorPlan
        exclude = ('created','updated')

class showvendorPlanSerializer(serializers.ModelSerializer):
    vendor = serializers.SerializerMethodField()
    class Meta:
        model = VendorPlan
        exclude = ('created','updated','sub_company')
    def get_vendor(self, obj):
        return {
            'id': obj.vendor.id,
            'name': obj.vendor.name,
        }


class showplanevendorInformation(serializers.ModelSerializer):
    vendor = serializers.CharField()
    sub_company=serializers.CharField()
    class Meta:
        model = VendorInformation
        exclude = ('created','updated')
from django.forms.models import model_to_dict

class showVendorInformationSerializer(serializers.ModelSerializer):
    vendor = serializers.SerializerMethodField()
    vendor_plan = serializers.SerializerMethodField()
    sub_company = serializers.CharField()
    class Meta:
        model = VendorInformation
        exclude = ('created','updated')
    def get_vendor(self, obj):
        return {
            'id': obj.vendor.id,
            'name': obj.vendor.name,
        }
    def get_vendor_plan(self, obj):
        if (not obj.vendor_plan) and obj.existing_plan:
            Vobj = BaselineDataTable.objects.exclude(banUploaded=None, banOnboarded=None).filter(sub_company=obj.sub_company.Organization_name,vendor=obj.vendor.name,plans=obj.existing_plan).first()
            print("obj==",Vobj)
            return {
                'id': None,
                'plan': Vobj.plans,
                'plan_type': Vobj.plan_type,
                'data_allotment': Vobj.data_allotment,
                'plan_fee': Vobj.plan_fee,
                'smartphone': Vobj.smartphone,
                'tablet_computer': Vobj.tablet_computer,
                'mifi': Vobj.mifi,
                'wearables': Vobj.wearables,
            } if Vobj else {}
        return {
            'id': obj.vendor_plan.id,
            'plan': obj.vendor_plan.plan,
            'plan_type': obj.vendor_plan.plan_type,
            'data_allotment': obj.vendor_plan.data_allotment,
            'plan_fee': obj.vendor_plan.plan_fee,
            'smartphone': obj.vendor_plan.smartphone,
            'tablet_computer': obj.vendor_plan.tablet_computer,
            'mifi': obj.vendor_plan.mifi,
            'wearables': obj.vendor_plan.wearables,
        } if obj.vendor_plan else None

class showOrganizations(serializers.ModelSerializer):
    vendors = serializers.SerializerMethodField()
    # sub_company_models = showMakeModelSerializer(read_only=True, many=True)
    # sub_company_devices = showdevicesSerializer(read_only=True, many=True)
    # sub_company_vendor_devices = showdevicesSerializer(read_only=True, many=True)
    # sub_company_vendor_info = showdevicesSerializer(read_only=True, many=True)
    class Meta:
        model = Organizations
        # fields = ('id','Organization_name','sub_company_devices','sub_company_models','sub_company_vendor_devices','sub_company_vendor_info')
        fields = ('id','Organization_name','vendors')

    def get_vendors(self, obj):
        return [{"id":vendor.id, "name":vendor.name} for vendor in obj.vendors.all()]




class showUsers(serializers.ModelSerializer):
    class Meta:
        model = PortalUser
        fields = ('id','first_name','last_name','email')
    

class AddusertoPortalSerializer(serializers.ModelSerializer):
    class Meta:
        model = PortalUser
        fields = "__all__"

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = PortalUser(**validated_data)
        user.set_password(password) 
        user.save()
        return user


class AddusertoProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = "__all__"

    
class OrganizationShowSerializer(serializers.ModelSerializer):
    vendors = serializers.StringRelatedField(many=True)
    locations = serializers.StringRelatedField(many=True)
    profile_vendors = serializers.SerializerMethodField()
    class Meta:
        model = Organizations
        fields = ['id', 'Organization_name', 'vendors', 'locations', 'profile_vendors']
    def get_profile_vendors(self,obj):
        profile = Profile.objects.filter(organization=obj).first()
        vendors = profile.vendors.all() if profile else None

        return [{"id":ven.id, "name":ven.name} for ven in vendors] if vendors else []


class VendorShowSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vendors
        fields = ['name','id']


import json
from addon import parse_until_dict
class showOnboardedSerializer(serializers.ModelSerializer):
    plans = serializers.SerializerMethodField()
    categories = serializers.SerializerMethodField()
    class Meta:
        model = BaseDataTable
        fields = ['accountnumber','vendor','sub_company','plans','categories']
    def get_plans(self, obj):
        distinct_plans = UniquePdfDataTable.objects.filter(
            viewuploaded=None,
            viewpapered=None,
            sub_company=obj.sub_company,
            vendor=obj.vendor,
            account_number=obj.accountnumber
        ).values_list('plans', flat=True).distinct()

        result = []
        for plan in distinct_plans:
            
            entry = UniquePdfDataTable.objects.filter(
                viewuploaded=None,
                viewpapered=None,
                sub_company=obj.sub_company,
                vendor=obj.vendor,
                account_number=obj.accountnumber,
                plans=plan
            ).values('plans', 'plan_type', 'mifi','data_allotment','plan_fee','smartphone','tablet_computer','wearables').first() if plan else None

            if entry:
                plan_name = entry.pop("plans")
                result.append({"plan": plan_name, **entry})


        return result

    def get_categories(self, obj):
        categories_qs = UniquePdfDataTable.objects.exclude(banOnboarded=None, banUploaded=None).filter(
            sub_company=obj.sub_company,
            vendor=obj.vendor,
            account_number=obj.accountnumber
        ).values_list('category_object', flat=True).distinct()

        merged = {}
        for category_dict in categories_qs:
            if not category_dict:
                continue
            category_dict = parse_until_dict(category_dict)
            for category, sub_dict in category_dict.items():
                if category not in merged:
                    merged[category] = set()
                merged[category].update(sub_dict.keys())

        result = [{"category": cat, "sub_categories": list(subs)} for cat, subs in merged.items()]
        return result


class showtrackinfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrackingInfo
        fields = '__all__'

class trackinfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrackingInfo
        fields = '__all__'

class showRequestSerializer(serializers.ModelSerializer):
    organization = OrganizationShowSerializer()
    requester = showUsers()
    vendor = VendorShowSerializer()
    tracking_pk = serializers.SerializerMethodField()
    class Meta:
        model = Requests
        fields = '__all__'
    
    def get_tracking_pk(self, obj):
        obj = TrackingInfo.objects.filter(request=obj.id).first()
        return showtrackinfoSerializer(obj).data if obj else None

from django.utils.dateparse import parse_datetime

class RequestsSaveSerializer(serializers.ModelSerializer):
    class Meta:
        model = Requests
        fields = '__all__'

class UniquePdfShowSerializer(serializers.ModelSerializer):
    class Meta:
        model = UniquePdfDataTable
        fields = ('user_name','account_number','vendor','sub_company','wireless_number')
 

class PhoneShowSerializer(serializers.ModelSerializer):
    class Meta:
        model = UniquePdfDataTable
        fields = "__all__"

class CostCentersShowSerializer(serializers.ModelSerializer):
    sub_company = serializers.CharField()
    vendor = serializers.CharField()
    class Meta:
        model = CostCenters
        exclude = ('created', 'updated')

class CostCentersSaveSerializer(serializers.ModelSerializer):
    class Meta:
        model = CostCenters
        fields = '__all__'

class EmployeeSerializer(serializers.ModelSerializer):
    sub_company = serializers.SerializerMethodField()
    vendor = serializers.SerializerMethodField()
    email = serializers.SerializerMethodField()
    designation = serializers.SerializerMethodField()
    user_id = serializers.SerializerMethodField()
    class Meta:
        model = UniquePdfDataTable
        exclude = ("category_object", "inventory")
    def get_user_id(self, obj):
        userObj = PortalUser.objects.filter(mobile_number=obj.wireless_number).first()
        return userObj.id
    def get_sub_company(self, obj):
        orgObj = Organizations.objects.filter(Organization_name=obj.sub_company).first()
        return {"id":orgObj.id, "Organization_name":orgObj.Organization_name}
    def get_vendor(self, obj):
        vendorObj = Vendors.objects.filter(name=obj.vendor).first()
        return {"id":vendorObj.id, "name":vendorObj.name}
    def get_email(self, obj):
        userObj = PortalUser.objects.filter(mobile_number=obj.wireless_number).first()
        return userObj.email
    def get_designation(self, obj):
        userObj = PortalUser.objects.filter(mobile_number=obj.wireless_number).first()
        return userObj.designation.name
    
from ..ModelsByPage.Req import upgrade_device_request

class SaveUpgradeDeviceRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = upgrade_device_request
        fields = "__all__"

class ShowUpgradeDeviceRequestSerializer(serializers.ModelSerializer):
    sub_company = serializers.SerializerMethodField()
    raised_by = serializers.SerializerMethodField()
    class Meta:
        model = upgrade_device_request
        fields = "__all__"
    def get_sub_company(self, obj):
        return {"id":obj.sub_company.id, "name":obj.sub_company.Organization_name}
    def get_raised_by(self, obj):
        return {"id":obj.raised_by.id, "first_name":obj.raised_by.first_name, "last_name":obj.raised_by.last_name, "email":obj.raised_by.email}
    