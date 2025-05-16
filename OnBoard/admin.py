from django.contrib import admin

# Register your models here.
from .Organization.models import Organizations
from .Company.models import Company


class OrganizationAdmin(admin.ModelAdmin):
    list_display = ('Organization_name', 'company', 'tax_id', 'Domain', 'created', 'updated')
    search_fields = ('Organization_name', 'tax_id', 'Domain')
    list_filter = ('created', 'updated')
    readonly_fields = ('created', 'updated')
    list_per_page = 10
    ordering = ('-created',)

class CompanyAdmin(admin.ModelAdmin):
    list_display = ('Company_name', 'created', 'updated')
    list_filter = ('created', 'updated')
    readonly_fields = ('created', 'updated')
    list_per_page = 10
    ordering = ('-created',)
# class ContractAdmin(admin.ModelAdmin):
#     list_display = ('organization', 'term', 'status')
#     search_fields = ('organization', 'term', 'status')
#     list_per_page = 10


admin.site.register(Organizations, OrganizationAdmin)
admin.site.register(Company, CompanyAdmin)

from .Location.models import BulkLocation, Location

@admin.register(BulkLocation)
class BulkLocationAdmin(admin.ModelAdmin):
    list_display = ('id', 'organization', 'file', 'created', 'updated')
    search_fields = ('organization__name',)
    list_filter = ('organization',)
    readonly_fields = ('created', 'updated')
    ordering = ('-created',)


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'site_name', 'company', 'organization', 'region', 'district',
        'state', 'country', 'primary_email', 'main_phone', 'created'
    )
    list_filter = (
        'organization', 'company', 'state', 'country', 'region', 'district', 'division'
    )
    search_fields = (
        'site_name', 'alias', 'primary_email', 'main_phone', 'mobile_number',
        'organization__name', 'company__name', 'state', 'region', 'district'
    )
    ordering = ('-created',)
    readonly_fields = ('created', 'updated')

    fieldsets = (
        ('Organizational Info', {
            'fields': ('company', 'organization', 'division', 'region', 'district', 'bulkfile')
        }),
        ('Location Identity', {
            'fields': ('site_name', 'alias', 'location_type', 'location_tax_id')
        }),
        ('Physical Address', {
            'fields': (
                'physical_address', 'physical_city', 'state', 'physical_zip_code',
                'country'
            )
        }),
        ('Mailing Address', {
            'fields': (
                'mail_address', 'mail_city', 'mail_state', 'mail_zip_code'
            )
        }),
        ('Contact Details', {
            'fields': (
                'primary_email', 'secondary_email', 'main_phone_code', 'main_phone',
                'main_fax_code', 'main_fax'
            )
        }),
        ('Personal Info', {
            'fields': (
                'first_name', 'last_name', 'title', 'did_number_code', 'did_number',
                'extension', 'mobile_code', 'mobile_number', 'mobile_status'
            )
        }),
        ('Media & Notes', {
            'fields': (
                'location_picture_1', 'location_picture_2',
                'location_picture_3', 'location_picture_4', 'notes'
            )
        }),
        ('Timestamps', {
            'fields': ('created', 'updated')
        }),
    )

from django.contrib import admin
from .Ban.models import (
    OnboardBan,
    InventoryUpload,
    MappingObjectBan,
    PdfDataTable
)

@admin.register(OnboardBan)
class OnboardBanAdmin(admin.ModelAdmin):
    list_display = ('organization', 'vendor', 'entryType', 'is_it_consolidatedBan', 'addDataToBaseline', 'created')
    search_fields = ('organization__Organization_name', 'vendor__name', 'uploadBill')
    list_filter = ('is_it_consolidatedBan', 'addDataToBaseline', 'entryType', 'billType', 'created')


@admin.register(InventoryUpload)
class InventoryUploadAdmin(admin.ModelAdmin):
    list_display = ('organization', 'vendor', 'ban', 'uploadFile', 'created')
    search_fields = ('organization__Organization_name', 'vendor__name', 'ban')
    list_filter = ('created',)


@admin.register(MappingObjectBan)
class MappingObjectBanAdmin(admin.ModelAdmin):
    list_display = ('account_number', 'vendor', 'wireless_number', 'user_name', 'created')
    search_fields = ('account_number', 'vendor', 'wireless_number', 'user_name', 'imei_number')
    list_filter = ('vendor', 'created')


@admin.register(PdfDataTable)
class PdfDataTableAdmin(admin.ModelAdmin):
    list_display = ('account_number', 'wireless_number', 'user_name', 'company', 'total_charges', 'created')
    search_fields = ('account_number', 'user_name', 'wireless_number', 'vendor', 'location')
    list_filter = ('vendor', 'company', 'created')
