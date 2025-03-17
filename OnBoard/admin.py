from django.contrib import admin

# Register your models here.
from .Organization.models import Organizations, Contract


class OrganizationAdmin(admin.ModelAdmin):
    list_display = ('Organization_name', 'company', 'tax_id', 'Domain', 'created', 'updated')
    search_fields = ('Organization_name', 'tax_id', 'Domain')
    list_filter = ('created', 'updated')
    readonly_fields = ('created', 'updated')
    list_per_page = 10
    ordering = ('-created',)


class ContractAdmin(admin.ModelAdmin):
    list_display = ('organization', 'term', 'status')
    search_fields = ('organization', 'term', 'status')
    list_per_page = 10


admin.site.register(Organizations, OrganizationAdmin)
admin.site.register(Contract, ContractAdmin)