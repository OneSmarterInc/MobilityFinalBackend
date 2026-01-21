from rest_framework import serializers
from .models import Reminder, Ticket
from authenticate.models import PortalUser

from Dashboard.ModelsByPage.DashAdmin import UserRoles
class PortalUserSerializer(serializers.ModelSerializer):
    designation = serializers.CharField(source='designation.name', read_only=True)
    company = serializers.CharField(source='company.Company_name', read_only=True)
    class Meta:
        model = PortalUser
        fields = ['email', 'first_name', 'last_name', 'designation', 'company','is_admin']

class ReminderSerializer(serializers.ModelSerializer):
    # to_roles = serializers.SlugRelatedField(
    #     many=True,
    #     slug_field='name',
    #     queryset=UserRoles.objects.all()
    # )
    to_roles = serializers.SerializerMethodField()
    class Meta:
        model = Reminder
        fields = '__all__'
    def get_to_roles(self, obj):
        # return id and name
        return list(obj.to_roles.values('id', 'name'))

class TicketSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = '__all__'

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        if not isinstance(rep.get('chat'), str):
            import json
            rep['chat'] = json.dumps(rep.get('chat', {}))
        return rep
    

    def create(self, validated_data):
        chat = validated_data.pop('chat', {})
        ticket = Ticket.objects.create(**validated_data)
        ticket.chat = chat
        ticket.save()
        return ticket

    def update(self, instance, validated_data):
        chat = validated_data.pop('chat', {})
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.chat = chat
        instance.save()
        return instance


from .models import BanHistory, WirelessHistory

class saveBanhistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = BanHistory
        fields = "__all__"

class showBanhistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = BanHistory
        fields = ("account_number", "user", "action", "timestamp")

class saveWirelesshistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = WirelessHistory
        fields = "__all__"

class showWirelesshistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = WirelessHistory
        fields = ("wireless_number", "user", "action", "timestamp")

from .models import PermissionsbyCompany
from Dashboard.ModelsByPage.DashAdmin import Permission

class PermissionShowSerializer(serializers.ModelSerializer):
    role = serializers.CharField(source='role.name')
    permissions = serializers.StringRelatedField(many=True)
    organization = serializers.SerializerMethodField()
    class Meta:
        model = UserRoles
        fields = ['role','permissions', 'organization']
    def get_organization(self, obj):
        return {"id":obj.organization.id, "name": obj.organization.Organization_name} if obj.organization else None
    

    def get_permissions(self, obj):
        return [permission.name for permission in obj.permissions.all()]
    
class permissionsSerializer(serializers.ModelSerializer):
    permissions = serializers.ListField(
        child=serializers.CharField(max_length=255),
        write_only=True,
        required=True
    )

    class Meta:
        model = PermissionsbyCompany
        fields = "__all__"
        read_only_fields = ['created', 'updated']

    def create(self, validated_data):
        print(validated_data)
        permissions_data = validated_data.pop('permissions', [])
        
        # Create instance first
        instance = PermissionsbyCompany.objects.create(**validated_data)
        
        # Attach permission objects
        if permissions_data:
            permissions = Permission.objects.filter(name__in=permissions_data)
            instance.permissions.set(permissions)
        
        instance.save()
        return instance
    def update(self, instance, validated_data):
        print("permissions", validated_data)
        permissions_data = validated_data.pop('permissions', None)

        # update all other fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        # if permissions key present (even if empty list), update relation
        if permissions_data is not None:
            permissions = Permission.objects.filter(name__in=permissions_data)
            instance.permissions.set(permissions)  # replaces old ones

        instance.save()
        return instance


    