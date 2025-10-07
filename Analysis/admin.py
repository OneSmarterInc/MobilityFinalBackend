from django.contrib import admin
from .models import Analysis, AnalysisData

@admin.register(Analysis)
class AnalysisAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'company', 'vendor', 'client', 'bill_date_info',
        'is_processed', 'created_by', 'created', 'updated'
    )
    list_filter = ('company', 'vendor', 'is_processed', 'created', 'created_by')
    search_fields = ('client', 'vendor__name', 'company__name', 'bill_date_info', 'created_by__username')
    readonly_fields = ('created', 'updated')
    date_hierarchy = 'created'
    ordering = ('-created',)

    fieldsets = (
        ('General Info', {
            'fields': ('company', 'vendor', 'client', 'remark', 'bill_date_info')
        }),
        ('Files', {
            'fields': ('uploadBill', 'excel')
        }),
        ('Status', {
            'fields': ('is_processed',)
        }),
        ('Audit Info', {
            'fields': ('created_by', 'created', 'updated')
        }),
    )

@admin.register(AnalysisData)
class AnalysisDataAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'analysis', 'account_number', 'bill_date', 'wireless_number', 'data_usage_range', 'user_name',
        'current_plan', 'current_plan_charges', 'current_plan_usage',
        'recommended_plan', 'recommended_plan_charges', 'recommended_plan_savings',
        'created', 'updated'
    )
    list_filter = ('data_usage_range', 'created', 'analysis__vendor')
    search_fields = ('wireless_number', 'user_name', 'current_plan', 'recommended_plan', 'analysis__client', 'account_number')
    readonly_fields = ('created', 'updated')
    date_hierarchy = 'created'
    ordering = ('-created',)

    fieldsets = (
        ('Analysis Info', {
            'fields': ('analysis',)
        }),
        ('User Info', {
            'fields': ('wireless_number', 'user_name')
        }),
        ('Current Plan Details', {
            'fields': ('data_usage_range', 'current_plan', 'current_plan_charges', 'current_plan_usage')
        }),
        ('Recommended Plan Details', {
            'fields': ('recommended_plan', 'recommended_plan_charges', 'recommended_plan_savings')
        }),
        ('Audit Info', {
            'fields': ('created', 'updated')
        }),
    )