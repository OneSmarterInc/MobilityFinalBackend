from django.contrib import admin
from .ModelsByPage.DashAdmin import *
# Register your models here.

from django.apps import apps

models = apps.get_models()

class RoleAdmin(admin.ModelAdmin):
    list_display = ('name', 'created', 'updated')
    search_fields = ('name', 'permissions')
    list_filter = ('created', 'updated')
    readonly_fields = ('created', 'updated')
    list_per_page = 10
    ordering = ('-created',)
    fields  = ('name', 'created', 'updated', 'permissions')



admin.site.register(UserRoles, RoleAdmin)

class OtherAdminpanels(admin.ModelAdmin):
    list_display = ('name', 'created', 'updated')
    search_fields = ('name',)
    list_filter = ('created', 'updated')
    readonly_fields = ('created', 'updated')
    list_per_page = 10
    ordering = ('-created',)

admin.site.register([EntryType, Vendors, BanStatus, InvoiceMethod, BanType, PaymentType, CostCenterLevel, CostCenterType, Permission, ManuallyAddedLocation, ManuallyAddedCompany], OtherAdminpanels)

