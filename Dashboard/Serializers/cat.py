from Dashboard.ModelsByPage.cat import BaselineCategories
from rest_framework import serializers

class showcategoriesSerializer(serializers.ModelSerializer):
    organization = serializers.SerializerMethodField()
    vendor = serializers.SerializerMethodField()
    class Meta:
        model = BaselineCategories
        fields = ("id","organization","vendor","ban","category","sub_categories")
    
    def get_organization(self,obj):
        return {"id":obj.organization.id, "name":obj.organization.Organization_name}
    
    def get_vendor(self,obj):
        return {"id":obj.vendor.id, "name":obj.vendor.name}

class catserializer(serializers.ModelSerializer):
    class Meta:
        model = BaselineCategories
        fields = '__all__'
        