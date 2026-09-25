from rest_framework import serializers
from .models import RiderFeedback, ProductRating
from Oders.models import Orders  # Verify exact app path


# ── RIDER FEEDBACK SERIALIZERS ───────────────────────────────────────

class RiderFeedbackSerializer(serializers.ModelSerializer):
    rider_name = serializers.CharField(
        source="rider.fullName",
        read_only=True
    )

    class Meta:
        model = RiderFeedback
        fields = [
            "id",
            "order",
            "rider",
            "rider_name",
            "rating",
            "comment",
            "created_at"
        ]
        read_only_fields = [
            "order",
            "rider",
            "created_at"
        ]

    def validate_rating(self, value):
        if value < 1 or value > 5:
            raise serializers.ValidationError(
                "Rating must be between 1 and 5."
            )
        return value


class RiderReviewSerializer(serializers.ModelSerializer):
    customer = serializers.CharField(
        source="user.username",
        read_only=True
    )

    class Meta:
        model = RiderFeedback
        fields = [
            "id",
            "customer",
            "rating",
            "comment",
            "created_at",
        ]


# ── PRODUCT RATING & REVIEW SERIALIZERS ──────────────────────────────

class ProductRatingSerializer(serializers.ModelSerializer):
    """
    Serializer used by customers to submit a rating/review for a delivered product.
    """
    customer_name = serializers.CharField(
        source="user.get_full_name",
        read_only=True
    )
    product_name = serializers.CharField(
        source="product.name",
        read_only=True
    )

    class Meta:
        model = ProductRating
        fields = [
            "id",
            "order",
            "product",
            "product_name",
            "customer_name",
            "rating",
            "review",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "created_at",
            "updated_at"
        ]

    def validate_rating(self, value):
        if value < 1 or value > 5:
            raise serializers.ValidationError(
                "Rating must be between 1 and 5 stars."
            )
        return value

    def validate(self, attrs):
        request = self.context.get("request")
        user = request.user
        order = attrs.get("order")
        product = attrs.get("product")

        # 1. Verify that the order belongs to the requesting customer
        if order.user != user:
            raise serializers.ValidationError(
                {"order": "You can only rate items from your own orders."}
            )

        # 2. Verify that the order status is DELIVERED
        order_status = getattr(order, "status", "").upper()
        if order_status != "DELIVERED":
            raise serializers.ValidationError(
                {"order": "Product ratings can only be submitted for delivered orders."}
            )

        # 3. Verify that the product was actually in this order
        if hasattr(order, "items"):
            order_product_ids = order.items.values_list("product_id", flat=True)
            if product.id not in order_product_ids:
                raise serializers.ValidationError(
                    {"product": "This product does not belong to the selected order."}
                )

        # 4. Check duplicate submission prevention
        if ProductRating.objects.filter(order=order, product=product, user=user).exists():
            raise serializers.ValidationError(
                "You have already submitted a rating for this product in this order."
            )

        return attrs


class ProductReviewSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer to render product reviews publicly on product detail pages.
    """
    customer = serializers.SerializerMethodField()

    class Meta:
        model = ProductRating
        fields = [
            "id",
            "customer",
            "rating",
            "review",
            "created_at",
        ]

    def get_customer(self, obj):
        # Displays full name if available, otherwise falls back to username/email
        if hasattr(obj.user, "get_full_name") and obj.user.get_full_name():
            return obj.user.get_full_name()
        return getattr(obj.user, "username", "Verified Buyer")