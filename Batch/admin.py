from django.contrib import admin

# Register your models here.
from .models import BatchAutomation, EmailConfiguration, Notification

@admin.register(BatchAutomation)
class BatchAutomationAdmin(admin.ModelAdmin):
    list_display = ('id', 'company_name', 'frequency', 'created_at', 'updated_at')
    search_fields = ('company_name', 'frequency')
    list_filter = ('frequency', 'created_at', 'updated_at')
    ordering = ('-created_at',)

@admin.register(EmailConfiguration)
class EmailConfigurationAdmin(admin.ModelAdmin):
    list_display = ('id', 'company', 'sender_name', 'sender_email', 'smtp_host', 'smtp_port', 'use_tls', 'use_ssl', 'created', 'updated')
    search_fields = ('company', 'sender_name', 'sender_email', 'smtp_host')
    list_filter = ('use_tls', 'use_ssl', 'created', 'updated')
    ordering = ('-created',)

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('id', 'company', 'description', 'created_at')
    search_fields = ('company', 'description')
    list_filter = ('created_at',)
    ordering = ('-created_at',)