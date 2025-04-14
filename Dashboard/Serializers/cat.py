from Dashboard.ModelsByPage.cat import BaselineCategories
from rest_framework import serializers

class catserializer(serializers.ModelSerializer):
    class Meta:
        model = BaselineCategories
        fields = '__all__'
        