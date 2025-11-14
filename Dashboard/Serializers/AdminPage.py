from rest_framework import serializers
from ..ModelsByPage.DashAdmin import Vendors, EntryType, BanStatus, InvoiceMethod, BanType, PaymentType, CostCenterLevel, CostCenterType, UserRoles, Permission, ManuallyAddedLocation, ManuallyAddedCompany, BillType


class VendorsOperationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vendors
        fields = '__all__'

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value) 
        instance.save()
        return instance



class VendorsShowSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vendors
        fields = ['name',]



class EntryTypeOperationSerializer(serializers.ModelSerializer):
    class Meta:
        model = EntryType
        fields = '__all__'

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value) 
        instance.save()
        return instance


class EntryTypeShowSerializer(serializers.ModelSerializer):
    class Meta:
        model = EntryType
        fields = ['name',]


class BanStatusOperationSerializer(serializers.ModelSerializer):
    class Meta:
        model = BanStatus
        fields = '__all__'

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value) 
        instance.save()
        return instance


class BanStatusShowSerializer(serializers.ModelSerializer):
    class Meta:
        model = BanStatus
        fields = ['name',]


class InvoiceMethodOperationSerializer(serializers.ModelSerializer):
    class Meta:
        model = InvoiceMethod
        fields = '__all__'
    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value) 
        instance.save()
        return instance


class InvoiceMethodShowSerializer(serializers.ModelSerializer):
    class Meta:
        model = InvoiceMethod
        fields = ['name',]


class BanTypeOperationSerializer(serializers.ModelSerializer):
    class Meta:
        model = BanType
        fields = '__all__'
    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value) 
        instance.save()
        return instance
    

class BanTypeShowSerializer(serializers.ModelSerializer):
    class Meta:
        model = BanType
        fields = ['name',]


class PaymentTypeOperationSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentType
        fields = '__all__'
    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value) 
        instance.save()
        return instance


class PaymentTypeShowSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentType
        fields = ['name',]


class CostCenterLevelOperationSerializer(serializers.ModelSerializer):
    class Meta:
        model = CostCenterLevel
        fields = '__all__'

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value) 
        instance.save()
        return instance


class CostCenterLevelShowSerializer(serializers.ModelSerializer):
    class Meta:
        model = CostCenterLevel
        fields = ['name',]


class CostCenterTypeOperationSerializer(serializers.ModelSerializer):
    class Meta:
        model = CostCenterType
        fields = '__all__'

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value) 
        instance.save()
        return instance


class CostCenterTypeShowSerializer(serializers.ModelSerializer):
    class Meta:
        model = CostCenterType
        fields = ['name',]

class saveBilltypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = BillType
        fields = '__all__'
        def update(self, instance, validated_data):
            for attr, value in validated_data.items():
                setattr(instance, attr, value) 
            instance.save()
            return instance
        
class BilltypeShowSerializer(serializers.ModelSerializer):
    class Meta:
        model = BillType
        fields = ['name',]

class PermissionOperationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permission
        fields = '__all__'
    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value) 
        instance.save()
        return instance


class PermissionShowSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permission
        fields = ['name',"Type"]



class UserRoleShowSerializer(serializers.ModelSerializer):
    permissions = serializers.StringRelatedField(many=True)
    class Meta:
        model = UserRoles
        fields = ['id','name','permissions', 'organization']

    def get_permissions(self, obj):
        return [permission.name for permission in obj.permissions.all()]
    
class UserRoleSaveSerializer(serializers.ModelSerializer):
    permissions = serializers.ListField(
        child=serializers.CharField(max_length=255),
        write_only=True,
        required=False  # Make permissions optional
    )

    class Meta:
        model = UserRoles
        fields = '__all__'
        read_only_fields = ['created', 'updated']

    def update(self, instance, validated_data):
        # Update 'name' field if present
        if 'name' in validated_data:
            instance.name = validated_data['name']
        
        # Update 'permissions' field if present
        if 'permissions' in validated_data:
            permissions_data = validated_data['permissions']
            permissions = Permission.objects.filter(name__in=permissions_data)
            instance.permissions.set(permissions)

        instance.save()
        return instance

class LocOperationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ManuallyAddedLocation
        fields = '__all__'
    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value) 
        instance.save()
        return instance


class LocShowSerializer(serializers.ModelSerializer):
    class Meta:
        model = ManuallyAddedLocation
        fields = ['name',]

class CompanyOperationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ManuallyAddedCompany
        fields = '__all__'
    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value) 
        instance.save()
        return instance


class CompanyShowSerializer(serializers.ModelSerializer):
    class Meta:
        model = ManuallyAddedCompany
        fields = ['name',]
        
class Vendorallserializer(serializers.ModelSerializer):
    class Meta:
        model = Vendors
        fields = '__all__'