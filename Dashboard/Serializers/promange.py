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
    designation = showrolename()
    class Meta:
        model = PortalUser
        fields = ['first_name', 'last_name','id','designation','username', 'email','phone_number','mobile_number']

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
    class Meta:
        model = Profile
        fields = '__all__'

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


        
        