from django.contrib import admin
from django.utils.html import format_html

from .models import AddToCart, Orders, OrderItem


# -----------------------------
# Cart
# -----------------------------
@admin.register(AddToCart)
class AddToCartAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "product",
        "quantity",
        "total_price",
        "updated_at",
    )

    search_fields = (
        "user__username",
        "user__email",
        "product__name",
    )

    list_filter = ("created_at",)
    autocomplete_fields = ("user", "product")
    readonly_fields = ("created_at", "updated_at")


# -----------------------------
# Order Item Inline
# -----------------------------
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0

    fields = (
        "product",
        "product_name",
        "quantity",
        "price",
        "total_amount",
    )

    readonly_fields = (
        "product_name",
        "price",
        "total_amount",
    )

    def total_amount(self, obj):
        return f"₹ {obj.total_price}"


# -----------------------------
# Orders
# -----------------------------
@admin.register(Orders)
class OrdersAdmin(admin.ModelAdmin):

    inlines = [OrderItemInline]

    list_display = (
        "order_id",
        "customer",
        "rider",
        "colored_status",
        "payment_status",
        "total",
        "created_at",
    )

    search_fields = (
        "order_id",
        "user__username",
        "user__email",
        "delivery_partner__fullName",
    )

    list_filter = (
        "status",
        "payment_status",
        "payment_method",
        "created_at",
    )

    date_hierarchy = "created_at"

    autocomplete_fields = (
        "user",
        "address",
        "delivery_partner",
    )

    readonly_fields = (
        "order_id",
        "subtotal",
        "delivery_fee",
        "total_amount",
        "payment_id",
        "created_at",
        "updated_at",
        "delivered_at",
    )

    fieldsets = (
        ("Order Information", {
            "fields": (
                "order_id",
                "status",
                "user",
                "delivery_partner",
                "address",
            )
        }),

        ("Payment", {
            "fields": (
                "payment_method",
                "payment_status",
                "payment_id",
            )
        }),

        ("Amount", {
            "fields": (
                "subtotal",
                "delivery_fee",
                "total_amount",
            )
        }),

        ("Timeline", {
            "fields": (
                "created_at",
                "updated_at",
                "delivered_at",
            )
        }),
    )

    # ---------- Custom Columns ----------

    def customer(self, obj):
        return obj.user.username

    customer.short_description = "Customer"

    def rider(self, obj):
        return obj.delivery_partner.fullName if obj.delivery_partner else "Not Assigned"

    rider.short_description = "Rider"

    def total(self, obj):
        return f"₹ {obj.total_amount}"

    total.short_description = "Total"

    def colored_status(self, obj):

        colors = {
            "pending": "#f59e0b",
            "accepted": "#2563eb",
            "packed": "#7c3aed",
            "picked": "#db2777",
            "ontheway": "#0d9488",
            "delivered": "#16a34a",
            "cancelled": "#dc2626",
        }

        color = colors.get(obj.status, "#6b7280")

        return format_html(
            '<span style="background:{};color:white;'
            'padding:4px 10px;border-radius:12px;'
            'font-weight:600;">{}</span>',
            color,
            obj.get_status_display()
        )

    colored_status.short_description = "Status"


# -----------------------------
# Order Items
# -----------------------------
@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "order",
        "product_name",
        "quantity",
        "price",
        "total",
    )

    search_fields = (
        "order__order_id",
        "product_name",
    )

    autocomplete_fields = (
        "order",
        "product",
    )

    def total(self, obj):
        return f"₹ {obj.total_price}"

    total.short_description = "Total"