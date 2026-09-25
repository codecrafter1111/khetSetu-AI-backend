from rest_framework import serializers
from .models import FarmerProfile, FarmDetail, FarmPhoto


class FarmPhotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = FarmPhoto
        fields = ["id", "image", "uploaded_at"]


class FarmDetailSerializer(serializers.ModelSerializer):
    photos = FarmPhotoSerializer(many=True, read_only=True)
    uploaded_photos = serializers.ListField(
        child=serializers.ImageField(max_length=1000000, allow_empty_file=False, use_url=False),
        write_only=True,
        required=False,
    )

    class Meta:
        model = FarmDetail
        fields = [
            "id", "farm_name", "farm_owner", "village", "district", "state", "pin_code",
            "farm_location_address", "latitude", "longitude", "total_farm_area", "area_unit",
            "soil_type", "farming_method", "irrigation_type", "water_source", "main_crops_grown",
            "has_organic_farming", "has_crop_rotation", "has_natural_fertilizers",
            "has_water_conservation", "has_soil_health_management", "has_integrated_pest_management",
            "has_agroforestry", "other_sustainability_practice", "photos", "uploaded_photos",
            "is_draft", "created_at", "updated_at",
        ]


class FarmerProfileSerializer(serializers.ModelSerializer):
    farm_detail = FarmDetailSerializer(read_only=True)

    class Meta:
        model = FarmerProfile
        fields = [
            "id", "full_name", "mobile_number", "email_address", "preferred_language",
            "state", "district", "village", "farming_experience", "short_bio",
            "is_draft", "is_verified", "verified_at", "rejection_reason",
            "farm_detail", "created_at", "updated_at",
        ]
        # Farmer user directly 'is_verified' status change nahi kar sakta
        read_only_fields = [
            "id", "is_verified", "verified_at", "verified_by", "rejection_reason",
            "created_at", "updated_at"
        ]


# Admin action perform karne ke liye alag Serializer
class AdminVerifyFarmerSerializer(serializers.ModelSerializer):
    class Meta:
        model = FarmerProfile
        fields = ["is_verified", "rejection_reason"]