from django.contrib import admin
from django.utils.html import format_html

from .models import CustomUser, BuyerShipping


@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "email",
        "username",
        "mobile_number",
        "role",
        "is_verified",
        
        "is_active",
        "date_joined",
    )

    list_filter = ("role","is_verified","is_active","is_staff","date_joined",)

    search_fields = ("email","username","mobile_number",)

    readonly_fields = ("last_login","date_joined",)

    ordering = ("-date_joined",)

    fieldsets = (
        ("Account Information", {
            "fields": ("username","email","password",)
        }),

        ("Personal Information", {
            "fields": ("mobile_number",)
        }),

        ("Role", {
            "fields": ("role","is_verified",)
        }),

        ("Permissions", {
            "fields": ("is_active","is_staff","is_superuser","groups","user_permissions",)
        }),

        ("Important Dates", {
            "fields": ("last_login","date_joined",)
        }),
    )




@admin.register(BuyerShipping)
class BuyerShippingAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "user",
        "full_name",
        "mobile_number",
        "city",
        "state",
        "zip_code",
        "address_type",
        "is_default",
        "created_at",
    )

    list_filter = (
        "address_type",
        "is_default",
        "state",
        "city",
    )

    search_fields = (
        "full_name",
        "mobile_number",
        "city",
        "state",
        "zip_code",
        "user__email",
    )

    readonly_fields = (
        "created_at",
    )

    ordering = ("-created_at",)