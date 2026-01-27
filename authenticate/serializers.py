from rest_framework import serializers
from django.contrib.auth.models import AbstractUser
from .models import PortalUser, UserLogs
from django.db.utils import IntegrityError
from django.contrib.auth.password_validation import validate_password
from Dashboard.ModelsByPage.DashAdmin import UserRoles, Permission, Vendors
from Settings.models import PermissionsbyCompany
from Dashboard.ModelsByPage.ProfileManage import Profile
from OnBoard.Ban.models import UniquePdfDataTable
from .signals import UserSignalThread
class banUsersSerializer(serializers.ModelSerializer):
    class Meta:
        model = UniquePdfDataTable
        fields = ("id","User_email","wireless_number","user_name")

from Dashboard.Serializers.AdminPage import UserRoleShowSerializer

class userSerializer(serializers.ModelSerializer):
    class Meta:
        model = PortalUser
        exclude = ("username",)

class RegisterSerializer(serializers.ModelSerializer):
    password2 = serializers.CharField(write_only=True)
    designation = serializers.CharField(required=False, allow_blank=True)
    company = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = PortalUser
        fields = ['username', 'email', 'password', 'password2', 'designation', 'company', 'first_name','last_name','phone_number','mobile_number','string_password','temp_password', 'organization', 'vendor','account_number','id']

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError("Passwords don't match.")
        return attrs

    def create(self, validated_data):
        # Remove password2 as it's not part of the model
        validated_data.pop('password2')

        # Extract designation as string if provided
        designation_name = validated_data.pop('designation', None)
        company_name = validated_data.pop('company', None)
        vendor_name = validated_data.pop('vendor',None)
        ban = validated_data.pop('account_number',None)



        # Create the user
        user = PortalUser.objects.create_user(**validated_data)

        # If designation is provided, get the UserRoles instance and assign it
        if designation_name:
            try:
                designation = UserRoles.objects.filter(organization=user.organization,name=designation_name).first()
                user.designation = designation
                user.save()
            except UserRoles.DoesNotExist:
                raise serializers.ValidationError(f"Designation '{designation_name}' does not exist.")
        
        if company_name:
            try:
                company = Company.objects.get(Company_name=company_name)
                user.company = company
                user.save()
            except Company.DoesNotExist:
                raise serializers.ValidationError(f"Company '{company_name}' does not exist.")
        if vendor_name:
            try:
                ven = Vendors.objects.get(name=vendor_name)
                user.vendor = ven
                
            except Vendors.DoesNotExist:
                raise serializers.ValidationError(f"Vendor '{vendor_name}' does not exist.")
            if not ban:
                raise serializers.ValidationError(f"Account number {ban} not found!")
            user.account_number = ban
            user.save()
        UserSignalThread(
            instance=user,
            company=user.company.Company_name if user.company else None,
            organization=user.organization.Organization_name if user.organization else None,
            role=user.designation.name if user.designation else None,
            username=user.username,
            email=user.email,
            pwd=user.string_password
        ).start()
        return user



class showUsersSerializer(serializers.ModelSerializer):
    designation = serializers.CharField(source='designation.name',max_length=255, read_only=True)
    company = serializers.CharField(max_length=255, read_only=True)
    organization = serializers.CharField(max_length=255, read_only=True)
    is_admin = serializers.SerializerMethodField()
    permissions = serializers.SerializerMethodField()
    all_wireless_numbers = serializers.SerializerMethodField()
    """
    Serializer to display user data.
    """
    class Meta:
        model = PortalUser
        fields = ['username', 'email', 'designation', 'company', 'organization', 'mobile_number', 'account_number', 'id','is_admin','permissions','first_name','last_name','all_wireless_numbers','is_active','is_notified']
    def get_is_admin(self, user):
        return not (user.vendor and user.account_number)
    def get_permissions(self,user):
        permissions = list(
            Permission.objects.filter(
                permissions_by_company__company=user.company,
                permissions_by_company__organization=user.organization,
                permissions_by_company__role=user.designation
            ).values_list('name', flat=True).distinct()
        )
        return permissions
    def get_all_wireless_numbers(self,user):
        return user.wireless_numbers.all().values("number","is_active","id")


class UserLogSaveSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserLogs
        fields = '__all__'

class UserLogShowSerializer(serializers.ModelSerializer):
    user = serializers.EmailField(source='user.email', read_only=True)
    class Meta:
        model = UserLogs
        fields = ['id', 'description', 'created_at', 'updated_at', 'user']

class allDesignationsSerializer(serializers.ModelSerializer):
    company = serializers.SerializerMethodField()
    organization = serializers.SerializerMethodField()
    class Meta:
        model = UserRoles
        fields = ['name','company','organization']
    def get_company(self,obj):
        return {"id":obj.company.id, "name":obj.company.Company_name}
    def get_organization(self,obj):
        return {"id":obj.organization.id, "name":obj.organization.Organization_name}

from OnBoard.Company.models import Company

class CompanyShowSerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = ['Company_name', ]

class EmailSerializer(serializers.Serializer):
    email = serializers.EmailField()

class OTPVerifySerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=6)