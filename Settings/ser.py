from rest_framework import serializers
from .models import Reminder, Ticket
from authenticate.models import PortalUser

class PortalUserSerializer(serializers.ModelSerializer):
    designation = serializers.CharField(source='designation.name', read_only=True)
    company = serializers.CharField(source='company.Company_name', read_only=True)
    class Meta:
        model = PortalUser
        fields = ['email', 'first_name', 'last_name', 'designation', 'company']
class ReminderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reminder
        fields = '__all__'
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


