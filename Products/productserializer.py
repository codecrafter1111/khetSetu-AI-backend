from rest_framework import serializers
from django.utils import timezone
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
        fields = ["id", "name"]
        read_only_fields = ['user']


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
    
    # ── TIMELINE / MANDATORY EXPIRY FIELD ────────────────────────────
    expiry_date = serializers.DateTimeField(
        required=True,
        allow_null=False,
        help_text="Mandatory expiry date for farm produce"
    )
    is_expired = serializers.BooleanField(read_only=True)

    class Meta:
        model = Products
        fields = [
            "uuid",
            "name",
            "slug",
            "category",
            "category_name",
            "brand",
            "image",
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
            "expiry_date",      # Mandatory input field
            "is_expired",       # Helper boolean flag
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "uuid",
            "slug",
            "is_available",
            "is_expired",
            "final_price",
            "offer_price",
            "created_at",
            "updated_at",
        ]

    def get_pr_small_url(self, obj):
        return get_pr_small_url(obj.image.public_id) if (obj.image and hasattr(obj.image, 'public_id')) else None

    def get_small_image(self, obj):
        return get_small_image(obj.image.public_id) if (obj.image and hasattr(obj.image, 'public_id')) else None

    def get_medium_image(self, obj):
        return get_medium_image(obj.image.public_id) if (obj.image and hasattr(obj.image, 'public_id')) else None

    def get_large_image(self, obj):
        return get_large_image(obj.image.public_id) if (obj.image and hasattr(obj.image, 'public_id')) else None

    def get_final_price(self, obj):
        return obj.final_price()

    def get_offer_price(self, obj):
        return obj.offer_price()

    def validate_stock(self, value):
        if value < 0:
            raise serializers.ValidationError("Stock negative nahi ho sakta.")
        return value

    def validate_offer(self, value):
        if value < 0 or value > 100:
            raise serializers.ValidationError("Offer percentage 0 aur 100 ke beech honi chahiye.")
        return value

    def validate_expiry_date(self, value):
        """Ensure expiry date is compulsory and must be in the future."""
        if not value:
            raise serializers.ValidationError("Expiry date daalna mandatory hai.")
            
        if value <= timezone.now():
            raise serializers.ValidationError("Expiry date future (aage ki date/time) ki honi chahiye.")
            
        return value