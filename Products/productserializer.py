from rest_framework import serializers
from .services.cloudnary_images import (
    get_small_image,
    get_medium_image,
    get_large_image,
    get_pr_small_url
)

from .models import Products, Categorys

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Categorys
        fields =["id","name",]
        
class ProductSerializer(serializers.ModelSerializer):

    category_name = serializers.CharField(
        source="category.name",
        read_only=True
    )
    pr_small_url = serializers.SerializerMethodField()
    small_image = serializers.SerializerMethodField()
    medium_image = serializers.SerializerMethodField()
    large_image = serializers.SerializerMethodField()

    final_price = serializers.SerializerMethodField()

    offer_price = serializers.SerializerMethodField()

    class Meta:
        model = Products

        fields = [
            "uuid",
            "name",
            "slug",

            "category",
            "category_name",

            "brand",
            "pr_small_url",
            "small_image",
            "medium_image",
            "large_image",

            "price_inr",

            "package_quantity",
            "package_unit",

            "offer",
            "offer_price",
            "final_price",

            "stock",
            "is_available",

            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "uuid",
            "slug",
            "is_available",
            "final_price",
            "offer_price",
            "created_at",
            "updated_at",
        ]

    def get_pr_small_url(self, obj):
        return get_pr_small_url(obj.image.public_id)
    def get_small_image(self, obj):
        return get_small_image(obj.image.public_id)

    def get_medium_image(self, obj):
        return get_medium_image(obj.image.public_id)

    def get_large_image(self, obj):
        return get_large_image(obj.image.public_id)

    
    def get_final_price(self, obj):
        return obj.final_price()

    def get_offer_price(self, obj):
        return obj.offer_price()

    def validate_stock(self, value):

        if value < 0:
            raise serializers.ValidationError(
                "Stock cannot be negative."
            )

        return value

    def validate_offer(self, value):

        if value < 0 or value > 100:
            raise serializers.ValidationError(
                "Offer must be between 0 and 100."
            )

        return value