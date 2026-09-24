from django.contrib import admin
from django.utils.html import format_html
from .models import (
    DeliveryPartner,
    PartnerDocuments,
    PartnerLocation,
    DeliveryAssignment,
    RiderEarning
)


# Inline document view inside DeliveryPartner Admin
class PartnerDocumentsInline(admin.StackedInline):
    model = PartnerDocuments
    can_delete = False
    extra = 0
    readonly_fields = ['document_preview']

    def document_preview(self, obj):
        html = ""
        if obj.Driving_licens:
            html += f"<b>License:</b> <a href='{obj.Driving_licens.url}' target='_blank'>View License</a><br/>"
        if obj.Vehicle_Rc:
            html += f"<b>RC:</b> <a href='{obj.Vehicle_Rc.url}' target='_blank'>View RC</a><br/>"
        if obj.Aadhar_docs:
            html += f"<b>Aadhar:</b> <a href='{obj.Aadhar_docs.url}' target='_blank'>View Aadhar</a><br/>"
        return format_html(html) if html else "No documents uploaded"


# Inline location view inside DeliveryPartner Admin
class PartnerLocationInline(admin.StackedInline):
    model = PartnerLocation
    can_delete = False
    extra = 0
    readonly_fields = ['updated_at']


@admin.register(DeliveryPartner)
class DeliveryPartnerAdmin(admin.ModelAdmin):
    list_display = [
        'Partner_id',
        'fullName',
        'mobile',
        'Vehicle_type',
        'Vehicle_number',
        'is_online',
        'is_available',
        'is_verified',
        'rating',
        'total_deliveries'
    ]
    list_filter = ['is_online', 'is_available', 'is_verified', 'Vehicle_type', 'created_at']
    search_fields = ['Partner_id', 'fullName', 'mobile', 'Vehicle_number', 'user__username']
    list_editable = ['is_online', 'is_available', 'is_verified']
    readonly_fields = ['created_at', 'rating', 'total_deliveries', 'avatar_preview']
    inlines = [PartnerDocumentsInline, PartnerLocationInline]

    def avatar_preview(self, obj):
        if obj.profile_image:
            return format_html(f'<img src="{obj.profile_image.url}" width="60" height="60" style="border-radius:50%;" />')
        return "No Image"
    avatar_preview.short_description = "Profile Image"


@admin.register(PartnerDocuments)
class PartnerDocumentsAdmin(admin.ModelAdmin):
    list_display = ['partner', 'verified', 'view_license', 'view_rc', 'view_aadhar']
    list_filter = ['verified']
    search_fields = ['partner__fullName', 'partner__Partner_id', 'partner__mobile']
    list_editable = ['verified']

    def view_license(self, obj):
        return format_html(f'<a href="{obj.Driving_licens.url}" target="_blank">View License</a>') if obj.Driving_licens else "-"
    
    def view_rc(self, obj):
        return format_html(f'<a href="{obj.Vehicle_Rc.url}" target="_blank">View RC</a>') if obj.Vehicle_Rc else "-"

    def view_aadhar(self, obj):
        return format_html(f'<a href="{obj.Aadhar_docs.url}" target="_blank">View Aadhar</a>') if obj.Aadhar_docs else "-"


@admin.register(PartnerLocation)
class PartnerLocationAdmin(admin.ModelAdmin):
    list_display = ['rider', 'latitude', 'longitude', 'updated_at']
    search_fields = ['rider__fullName', 'rider__Partner_id', 'rider__mobile']
    readonly_fields = ['updated_at']


@admin.register(DeliveryAssignment)
class DeliveryAssignmentAdmin(admin.ModelAdmin):
    list_display = ['order', 'rider', 'status', 'assigned_at', 'delivered_at']
    list_filter = ['status', 'assigned_at']
    search_fields = ['order__order_id', 'rider__fullName', 'rider__Partner_id']
    list_editable = ['status']
    readonly_fields = ['assigned_at']


@admin.register(RiderEarning)
class RiderEarningAdmin(admin.ModelAdmin):
    list_display = ['rider', 'order', 'delivery_fee', 'tip', 'get_total', 'created_at']
    list_filter = ['created_at']
    search_fields = ['rider__fullName', 'order__order_id']
    readonly_fields = ['created_at']

    def get_total(self, obj):
        return float(obj.delivery_fee or 0) + float(obj.tip or 0)
    get_total.short_description = "Total Payout"