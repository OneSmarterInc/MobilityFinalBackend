from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import viewPaperBill, ViewUploadBill, ProcessedWorkbook

@admin.register(viewPaperBill)
class ViewPaperBillAdmin(admin.ModelAdmin):
    list_display = ('account_number', 'wireless_number', 'invoice_number', 'user_name', 'invoice_date', 'due_date', 'monthly_bill', 'company', 'organization', 'vendor', 'created_at', 'updated_at')
    search_fields = ('account_number', 'invoice_number', 'user_name')
    list_filter = ('company', 'organization', 'vendor', 'invoice_date', 'due_date')
    ordering = ('-created_at',)

@admin.register(ViewUploadBill)
class ViewUploadBillAdmin(admin.ModelAdmin):
    list_display = ('file_type', 'file', 'company', 'organization', 'vendor', 'month', 'year', 'types', 'output_file', 'created_at', 'updated_at')
    search_fields = ('file_type', 'month', 'year')
    list_filter = ('company', 'organization', 'vendor', 'month', 'year')
    ordering = ('-created_at',)

@admin.register(ProcessedWorkbook)
class ProcessedWorkbookAdmin(admin.ModelAdmin):
    list_display = ('account_number', 'vendor_name', 'company_name', 'sub_company_name', 'workbook_name', 'bill_date_info', 'output_file', 'created_at', 'updated_at')
    search_fields = ('account_number', 'vendor_name', 'company_name', 'sub_company_name', 'workbook_name')
    list_filter = ('vendor_name', 'company_name', 'bill_date_info')
    ordering = ('-created_at',)

