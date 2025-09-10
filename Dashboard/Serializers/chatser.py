
from rest_framework import serializers
from ..ModelsByPage.aimodels import BotChats

class ChatSerializer(serializers.ModelSerializer):
    class Meta:
        model = BotChats
        fields = ("question","response","created_at")