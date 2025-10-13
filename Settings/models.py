from django.db import models
from django.utils import timezone
from OnBoard.Company.models import Company
from Dashboard.ModelsByPage.DashAdmin import UserRoles
# Create your models here.

class Ticket(models.Model):
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        default=None,
        null=True,
        blank=True, 
        related_name="companytickets",  
    )
    issue_type = models.CharField(max_length=100, null=True, blank=True)
    sub_company = models.CharField(max_length=100, null=True, blank=True)
    vendor = models.CharField(max_length=100, null=True, blank=True)
    company = models.CharField(max_length=100, null=True, blank=True)
    account_no = models.CharField(max_length=100, null=True, blank=True)
    message = models.CharField(max_length=500, null=True, blank=True)
    description = models.CharField(max_length=1000, null=True, blank=True)
    assign_email = models.EmailField(null=True, blank=True)
    key = models.CharField(max_length=20, null=True, blank=True)
    
    PRIORITY_CHOICES = [
        (1, 'Low'),
        (2, 'Medium'),
        (3, 'High'),
        (4, 'Critical'),
    ]

    priority = models.IntegerField(
        null=True, blank=True, choices=PRIORITY_CHOICES)
    in_process = models.BooleanField(default=True)
    is_hold = models.BooleanField(default=False)
    is_resolved = models.BooleanField(default=False)
    is_closed = models.BooleanField(default=False)
    user_email = models.EmailField(null=True, blank=True)
    chat = models.JSONField(null=True, blank=True, default=dict)
    created_at = models.DateTimeField(default=timezone.now)
    #ticket_number = models.CharField(max_length=36, unique=True, editable=False, null=True, blank=True)


    


    def add_message_to_chat(self, sender, message):
        if not self.chat:
            self.chat = {"chat": []}
        self.chat["chat"].append({
            "sender": sender,
            "timestamp": timezone.now().isoformat(),
            "message": message
        })
        self.save()

    def _str_(self):
        return f"Ticket {self.id}: {self.sub_company} - {self.vendor}"
    
    class Meta:
        db_table = 'Ticket'

class Reminder(models.Model):
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        default=None,
        null=True,
        blank=True, 
        related_name="companyreminders",  
    )
    title = models.CharField(max_length=100, null=True, blank=True)
    description = models.CharField(max_length=100, null=True, blank=True)
    date = models.CharField(max_length=100, null=True, blank=True)
    time = models.CharField(max_length=100, null=True, blank=True)
    log_email = models.CharField(max_length=100, null=True, blank=True)
    weekly_Reminders = models.JSONField(null=True, blank=True, default=dict)
    reminder_type = models.CharField(max_length=100, null=True, blank=True)
    to_roles = models.ManyToManyField(UserRoles, blank=True)

    def __str__(self):
        return self.title
    
    class Meta:
        db_table = 'Reminder'