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
            "dates",
            "emails",
            "created_by_id",
            "created_by_email",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate(self, attrs):
        frequency = attrs.get(
            "frequency",
            getattr(self.instance, "frequency", None)
        )

        days = attrs.get(
            "days",
            getattr(self.instance, "days", [])
        )

        dates = attrs.get(
            "dates",
            getattr(self.instance, "dates", [])
        )

        valid_days = [
            "Monday", "Tuesday", "Wednesday",
            "Thursday", "Friday", "Saturday", "Sunday"
        ]

        # ---------- DAILY ----------
        if frequency == BatchAutomation.FREQ_DAILY:
            names = [d.get("day") for d in days]

            if sorted(names) != sorted(valid_days):
                raise serializers.ValidationError({
                    "days": "Daily frequency requires all 7 days."
                })

            if dates:
                raise serializers.ValidationError({
                    "dates": "Dates are not allowed for daily frequency."
                })

        # ---------- WEEKLY ----------
        elif frequency == BatchAutomation.FREQ_WEEKLY:
            if not days or len(days) < 1:
                raise serializers.ValidationError({
                    "days": "Weekly frequency requires at least one day."
                })

            for d in days:
                if d.get("day") not in valid_days:
                    raise serializers.ValidationError({
                        "days": f"Invalid weekday: {d.get('day')}"
                    })

            if dates:
                raise serializers.ValidationError({
                    "dates": "Dates are not allowed for weekly frequency."
                })

        # ---------- SPECIFIC ----------
        elif frequency == BatchAutomation.FREQ_SPECIFIC:
            if days:
                raise serializers.ValidationError({
                    "days": "Days must be empty for specific frequency."
                })

            if not dates or len(dates) != 1:
                raise serializers.ValidationError({
                    "dates": "Specific frequency requires exactly one date."
                })

            date_val = dates[0].get("date")
            if not isinstance(date_val, int) or not (1 <= date_val <= 31):
                raise serializers.ValidationError({
                    "dates": "Date must be an integer between 1 and 31."
                })

        else:
            raise serializers.ValidationError({
                "frequency": "Invalid frequency."
            })

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