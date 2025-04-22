from rest_framework import serializers
from ..models import PortalInformation

class showPortalInfoser(serializers.ModelSerializer):
    class Meta:
        model = PortalInformation
        fields = '__all__'