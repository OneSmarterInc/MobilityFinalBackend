from rest_framework import serializers
from OnBoard.Ban.models import UniquePdfDataTable
from ..ModelsByPage.DashAdmin import UserRoles
from OnBoard.Organization.models import Organizations
from authenticate.models import PortalUser
from ..ModelsByPage.ProfileManage import Profile
from Dashboard.ModelsByPage.DashAdmin import Permission
class OrganizationsShowSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organizations
        fields = ['id', 'Organization_name',]
        
class showdesignations(serializers.ModelSerializer):
    class Meta:
        model = UserRoles
        fields = '__all__'

class showrolename(serializers.ModelSerializer):
    class Meta:
        model = UserRoles
        fields = ['name',]
class showusers(serializers.ModelSerializer):
    organization = serializers.SerializerMethodField()
    vendors = serializers.SerializerMethodField()
    designation = showrolename()
    class Meta:
        model = PortalUser
        fields = ['first_name', 'last_name','id','designation','username', 'email','phone_number','mobile_number','organization','vendors']
    def get_vendors(self,obj):
        profile_obj = Profile.objects.filter(user=obj).first()

        if profile_obj:
            vendors = profile_obj.vendors.all()
            return [{"id":vendor.id, "name":vendor.name} for vendor in vendors]  if vendors else []
        else: return []
        
    def get_organization(self,obj):
        profile_obj = Profile.objects.filter(user=obj).first()
        return {"id":profile_obj.organization.id, "name": profile_obj.organization.Organization_name} if profile_obj else {"id":"", "name":""}

class ProfileSaveSerializer(serializers.ModelSerializer):
    permissions = serializers.ListField(
        child=serializers.CharField(max_length=255),
        write_only=True,
        required=False
    )

    class Meta:
        model = Profile
        fields = '__all__'

    def update(self, instance, validated_data):
        if 'permissions' in validated_data:
            permissions_data = validated_data.pop('permissions')
            permissions = Permission.objects.filter(name__in=permissions_data)
            instance.permissions.set(permissions)

        if 'vendors' in validated_data:
            vendors_data = validated_data.pop('vendors')
            instance.vendors.set(vendors_data)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance



class usersShowser(serializers.ModelSerializer):
    class Meta:
        model = PortalUser
        fields = ['first_name', 'last_name','id']

class roleser(serializers.ModelSerializer):
    class Meta:
        model = UserRoles
        fields = ['name','id']

class ProfileShowSerializer(serializers.ModelSerializer):
    organization = serializers.CharField()
    user = usersShowser()
    role = roleser()
    vendors = serializers.SerializerMethodField()
    class Meta:
        model = Profile
        fields = '__all__'
    def get_vendors(self,obj):
        vendors = obj.vendors.all()
        return [{"id":vendor.id, "name":vendor.name} for vendor in vendors] if vendors else []

class PermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permission
        fields = ('name','Type')
class ProfilePermissionSerializer(serializers.ModelSerializer):
    role = serializers.CharField(source='role.name')
    permissions = serializers.SlugRelatedField(
        many=True,
        read_only=True,
        slug_field='name'  
    )

    class Meta:
        model = Profile
        fields = ('permissions', 'role')

class GetUserbyOrgSerializer(serializers.ModelSerializer):
    organization = serializers.CharField()
    role = serializers.SerializerMethodField()
    user = serializers.SerializerMethodField()
    class Meta:
        model = Profile
        exclude = ("usertype",)
    def get_role(self,obj):
        return obj.role.name
    def get_user(self,obj):
        return f'{obj.user.first_name} {obj.user.last_name}'