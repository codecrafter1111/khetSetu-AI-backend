from rest_framework import serializers
from .models import RiderFeedback

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