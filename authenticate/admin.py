from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import PortalUser, UserLogs
from django.utils.translation import gettext_lazy as _

@admin.register(PortalUser)
class PortalUserAdmin(UserAdmin):
    model = PortalUser

    list_display = (
        "username", 
        "email", 
        "first_name", 
        "last_name", 
        "designation", 
        "company", 
        "phone_number", 
        "mobile_number",
        "is_staff", 
        "is_active"
    )

    list_filter = (
        "is_staff", 
        "is_superuser", 
        "is_active", 
        "designation", 
        "company"
    )

    search_fields = (
        "username", 
        "email", 
        "first_name", 
        "last_name", 
        "phone_number", 
        "mobile_number"
    )

    ordering = ("email",)

    fieldsets = (
        (None, {"fields": ("username", "password")}),
        (_("Personal Info"), {
            "fields": (
                "first_name", 
                "last_name", 
                "email", 
                "designation", 
                "company", 
                "phone_number", 
                "mobile_number", 
                "contact_type"
            )
        }),
        (_("Permissions"), {
            "fields": (
                "is_active", 
                "is_staff", 
                "is_superuser", 
                "groups", 
                "user_permissions"
            )
        }),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": (
                "username",
                "email",
                "password1",
                "password2",
                "first_name",
                "last_name",
                "designation",
                "company",
                "phone_number",
                "mobile_number",
                "contact_type",
                "is_staff",
                "is_active",
            ),
        }),
    )
@admin.register(UserLogs)
class UserLogsAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'description', 'created_at', 'updated_at')
    search_fields = ('user__email', 'user__username', 'description')
    list_filter = ('user', 'created_at')
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)