from rest_framework import serializers
from .models import BatchAutomation,EmailConfiguration
from OnBoard.Organization.models import Organizations

class DayProductionSerializer(serializers.Serializer):
    day = serializers.ChoiceField(choices=["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"])
    production = serializers.BooleanField()


class BatchAutomationSerializer(serializers.ModelSerializer):
    # Denormalized fields only
    company_id = serializers.IntegerField()
    company_name = serializers.CharField(allow_blank=True, required=False)
    days = DayProductionSerializer(many=True)
    emails = serializers.ListField(child=serializers.EmailField())

    class Meta:
        model = BatchAutomation
        fields = [
            "id",
            "company_id",
            "company_name",
            "frequency",
            "days",
            "emails",
            "created_by_id",
            "created_by_email",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate(self, attrs):
        frequency = attrs.get("frequency", getattr(self.instance, "frequency", None))
        days = attrs.get("days", getattr(self.instance, "days", []))
        valid_days = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
        names = [d["day"] for d in days]

        if frequency == BatchAutomation.FREQ_DAILY:
            if sorted(names) != sorted(valid_days):
                raise serializers.ValidationError("Daily frequency requires all 7 days.")
        elif frequency == BatchAutomation.FREQ_WEEKLY:
            if len(days) < 1:
                raise serializers.ValidationError("Weekly frequency requires at least one day.")
        elif frequency == BatchAutomation.FREQ_SPECIFIC:
            if len(days) != 1:
                raise serializers.ValidationError("Specific frequency requires exactly one day.")
        else:
            raise serializers.ValidationError("Invalid frequency.")
        return attrs

    def create(self, validated_data):
        sub_company_id = validated_data.pop("sub_company", None) or validated_data.get("company_id", None)
        if sub_company_id:
            try:
                sub_company = Organizations.objects.get(id=sub_company_id)
                validated_data["sub_company"] = sub_company
            except Organizations.DoesNotExist:
                raise serializers.ValidationError("Invalid sub_company ID.")
        return BatchAutomation.objects.create(**validated_data)

    def update(self, instance, validated_data):
        for k, v in validated_data.items():
            setattr(instance, k, v)
        instance.save()
        return instance
    
    
    

class EmailConfigurationSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmailConfiguration
        fields = '__all__'    