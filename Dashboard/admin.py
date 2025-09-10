from django.contrib import admin
from .ModelsByPage.DashAdmin import *
from .ModelsByPage.ProfileManage import Profile
from .ModelsByPage.cat import BaselineCategories
from .ModelsByPage.aimodels import BotChats
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

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('id', 'organization', 'user', 'usertype', 'role', 'email', 'phone')
    list_filter = ('organization', 'usertype', 'role')
    search_fields = (
        'user__username', 'user__email', 'organization__name', 'email', 'phone', 'role__name'
    )
    filter_horizontal = ('permissions',)  # Better UI for ManyToManyField
    ordering = ('organization', 'user')

    fieldsets = (
        ('User Details', {
            'fields': ('organization', 'user', 'usertype', 'role')
        }),
        ('Contact Info', {
            'fields': ('email', 'phone')
        }),
        ('Permissions', {
            'fields': ('permissions',)
        }),
    )

@admin.register(BaselineCategories)
class BaselineCategoriesAdmin(admin.ModelAdmin):
    list_display = ('id', 'category', 'display_subcategories')
    search_fields = ('category',)
    ordering = ('category',)

    # Custom method to neatly display JSON list in the admin list view
    def display_subcategories(self, obj):
        return ', '.join(obj.sub_categories) if obj.sub_categories else '-'
    display_subcategories.short_description = 'Sub Categories'

@admin.register(BotChats)
class BotChatsAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'short_question', 'short_response', 'created_at')
    search_fields = ('user__username', 'question', 'response')
    list_filter = ('created_at',)
    ordering = ('-created_at',)

    def short_question(self, obj):
        return (obj.question[:75] + '...') if len(obj.question) > 75 else obj.question
    short_question.short_description = 'Question'

    def short_response(self, obj):
        return (obj.response[:75] + '...') if len(obj.response) > 75 else obj.response
    short_response.short_description = 'Response'