from django.contrib import admin
from .models import Categorys, Products, ShopLocation


@admin.register(Categorys)
class CategorysAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(Products)
class ProductsAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "brand",
        "category",
        "price_inr",
        "stock",
        "is_available",
    )

    search_fields = (
        "name",
        "brand",
        "slug",
    )

    list_filter = (
        "category",
        "brand",
        "is_available",
    )


@admin.register(ShopLocation)
class ShopLocationAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "address",
        "latitude",
        "longitude",
    )

    search_fields = (
        "name",
        "address",
    )

    list_filter = ()