from rest_framework import serializers
from OnBoard.Location.models import Location

from OnBoard.Ban.models import BaseDataTable, UniquePdfDataTable
class OrganizationLocationSerializer(serializers.ModelSerializer):
    company = serializers.CharField()
    organization = serializers.CharField()
    division = serializers.CharField()
    class Meta:
        model = Location
        exclude = ("location_picture_1", "location_picture_2","location_picture_3","location_picture_4", "created", "updated")



class InventorySerializer(serializers.ModelSerializer):
    
    location = serializers.SerializerMethodField()
    gl_code = serializers.SerializerMethodField()
    banstatus = serializers.SerializerMethodField()
    class Meta:
        model = UniquePdfDataTable
        fields = ("company","sub_company", "vendor","account_number", "wireless_number","location","gl_code","banstatus")
    def _filterObj(self, obj):
        return BaseDataTable.objects.filter(banUploaded=obj.banUploaded,banOnboarded=obj.banOnboarded).first()
    def get_location(self, wireless):
        loc = self._filterObj(wireless)
        return loc.location if loc else ""
    def get_gl_code(self, wireless):
        glcode = self._filterObj(wireless)
        return glcode.GlCode if glcode else ""
    def get_banstatus(self, wireless):
        bs = self._filterObj(wireless)
        return bs.banstatus if bs else ""

    
    
    