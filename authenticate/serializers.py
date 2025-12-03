from rest_framework import serializers
from django.contrib.auth.models import AbstractUser
from .models import PortalUser, UserLogs
from django.db.utils import IntegrityError
from django.contrib.auth.password_validation import validate_password
from Dashboard.ModelsByPage.DashAdmin import UserRoles, Permission
from Settings.models import PermissionsbyCompany
from Dashboard.ModelsByPage.ProfileManage import Profile

from Dashboard.Serializers.AdminPage import UserRoleShowSerializer

class userSerializer(serializers.ModelSerializer):
    class Meta:
        model = PortalUser
        fields = "__all__"

class RegisterSerializer(serializers.ModelSerializer):
    password2 = serializers.CharField(write_only=True)
    designation = serializers.CharField(required=False, allow_blank=True)
    company = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = PortalUser
        fields = ['username', 'email', 'password', 'password2', 'designation', 'company', 'first_name','last_name','phone_number','mobile_number','string_password','temp_password', 'organization']

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

        return user



class showUsersSerializer(serializers.ModelSerializer):
    designation = serializers.CharField(source='designation.name',max_length=255, read_only=True)
    company = serializers.CharField(max_length=255, read_only=True)
    organization = serializers.CharField(max_length=255, read_only=True)
    is_admin = serializers.SerializerMethodField()
    permissions = serializers.SerializerMethodField()
    """
    Serializer to display user data.
    """
    class Meta:
        model = PortalUser
        fields = ['username', 'email', 'designation', 'company', 'organization', 'mobile_number', 'account_number', 'id','is_admin','permissions']
    def get_is_admin(self, user):
        return "admin" in user.designation.name.lower() if user.designation else True
    def get_permissions(self,user):
        print(user.company, user.organization, user.designation)
        xyz = PermissionsbyCompany.objects.filter(company=user.company, organization=user.organization, role=user.designation)
        print(xyz)
        permissions = list(
            Permission.objects.filter(
                permissions_by_company__company=user.company,
                permissions_by_company__organization=user.organization,
                permissions_by_company__role=user.designation
            ).values_list('name', flat=True).distinct()
        )
        print(permissions)
        return permissions


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