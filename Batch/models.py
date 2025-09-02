from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

# Create your models here.


class BatchAutomation(models.Model):
    FREQ_DAILY = "daily"
    FREQ_WEEKLY = "weekly"
    FREQ_SPECIFIC = "specific"
    FREQ_CHOICES = [
        (FREQ_DAILY, "Daily"),
        (FREQ_WEEKLY, "Weekly"),
        (FREQ_SPECIFIC, "Specific"),
    ]

    # Denormalized company info (no FK)
    company_id = models.IntegerField(help_text="Organization id from external source/UI")
    company_name = models.CharField(max_length=255, blank=True, default="")

    frequency = models.CharField(max_length=16, choices=FREQ_CHOICES)

    # [{ "day": "Monday", "production": true }, ...]
    days = models.JSONField(default=list)

    # ["ops@example.com", "team@example.com"]
    emails = models.JSONField(blank=True, default=list)

    # Optional denormalized creator info (no FK)
    created_by_id = models.IntegerField(null=True, blank=True)
    created_by_email = models.EmailField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.company_name or self.company_id} - {self.frequency}"

    def clean(self):
        valid_days = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]

        if not isinstance(self.days, list):
            raise ValidationError({"days": "Must be a list of objects {day, production}."})

        seen = set()
        for i, d in enumerate(self.days):
            if not isinstance(d, dict):
                raise ValidationError({"days": f"Item {i} must be an object."})
            day = d.get("day")
            production = d.get("production")
            if day not in valid_days:
                raise ValidationError({"days": f"Invalid day '{day}' at index {i}."})
            if not isinstance(production, bool):
                raise ValidationError({"days": f"'production' must be boolean at index {i}."})
            if day in seen:
                raise ValidationError({"days": f"Duplicate day '{day}'."})
            seen.add(day)

        if self.frequency == self.FREQ_DAILY:
            if sorted([d["day"] for d in self.days]) != sorted(valid_days):
                raise ValidationError({"days": "Daily frequency requires all 7 days."})
        elif self.frequency == self.FREQ_WEEKLY:
            if len(self.days) < 1:
                raise ValidationError({"days": "Weekly frequency requires at least one day."})
        elif self.frequency == self.FREQ_SPECIFIC:
            if len(self.days) != 1:
                raise ValidationError({"days": "Specific frequency requires exactly one day."})
        else:
            raise ValidationError({"frequency": "Invalid frequency."})

        if not isinstance(self.emails, list) or not all(isinstance(e, str) for e in self.emails):
            raise ValidationError({"emails": "Emails must be a list of strings."})

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)
    
    
    
from OnBoard.Organization.models import Organizations
class EmailConfiguration(models.Model):
    sub_company = models.ForeignKey(Organizations, related_name='organization_configuration', on_delete=models.CASCADE, null=True, blank=True)
   
    company = models.CharField(max_length=255, null=False, blank=False)
    organization = models.CharField(max_length=255, null=True, blank=True)
    sender_name = models.CharField(max_length=255, null=True, blank=True)
    sender_email = models.CharField(max_length=255, null=True, blank=True)
    smtp_host = models.CharField(max_length=255, null=True, blank=True)
    smtp_port = models.CharField(max_length=255, null=True, blank=True)
    password = models.CharField(max_length=255, null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    use_tls = models.BooleanField(default=False)   # STARTTLS (typical for 587)
    use_ssl = models.BooleanField(default=False)  
    class Meta:
        db_table = 'EmailConfiguration'
    
    def __str__(self):
        return f'{self.company} - {self.sender_name}'


    