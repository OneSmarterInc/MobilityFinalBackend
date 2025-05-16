from django.contrib import admin
from .models import Analysis

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
