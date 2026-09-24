from django.contrib import admin
from .models import Categorys,Products

@admin.register(Categorys)
class CategorysAdmin(admin.ModelAdmin):
  list_display =['name']
# Register your models here.

from django.contrib import admin
from .models import Products

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