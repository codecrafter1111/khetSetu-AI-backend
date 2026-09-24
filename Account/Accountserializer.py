
from rest_framework import serializers
from .models import CustomUser
import re
from Products.services.cloudnary_images import get_pr_small_url

class CustomUserSerializer(serializers.ModelSerializer):

    confirm_password = serializers.CharField(
        write_only=True
    )
    pr_small_url = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser

        fields = [
            "id",
            "username",
            "email",
            "password",
            "confirm_password",
            "mobile_number",
            "role",
            "profile_image",
            "pr_small_url",
        ]

        extra_kwargs = {
            "password": {
                "write_only": True
            }
        }

    # -------------------------
    # Object-level validation
    # -------------------------

    def get_pr_small_url(self, obj):
            return get_pr_small_url(obj.profile_image.public_id)
    
    def validate(self, attrs):

        if attrs["password"] != attrs["confirm_password"]:
            raise serializers.ValidationError({
                "confirm_password": "Passwords do not match."
            })

        return attrs

    # -------------------------
    # Email validation
    # -------------------------

    def validate_email(self, value):

        value = value.lower().strip()

        if CustomUser.objects.filter(
            email__iexact=value
        ).exists():

            raise serializers.ValidationError(
                "Email already exists."
            )

        if not value.endswith("@gmail.com"):

            raise serializers.ValidationError(
                "Email must be a Gmail address."
            )

        return value

    # -------------------------
    # Username validation
    # -------------------------

    def validate_username(self, value):

        value = value.strip()

        if len(value) < 3:

            raise serializers.ValidationError(
                "Username must be at least 3 characters long."
            )

        if not re.match(
            r"^[a-zA-Z0-9_]+$",
            value
        ):

            raise serializers.ValidationError(
                "Username can contain only letters, numbers and underscores."
            )

        if CustomUser.objects.filter(
            username__iexact=value
        ).exists():

            raise serializers.ValidationError(
                "Username already exists."
            )

        return value

    # -------------------------
    # Password validation
    # -------------------------

    def validate_password(self, value):

        if len(value) < 6:

            raise serializers.ValidationError(
                "Password must be at least 6 characters long."
            )

        return value

    # -------------------------
    # Mobile validation
    # -------------------------

    def validate_mobile_number(self, value):

        if not value.isdigit():

            raise serializers.ValidationError(
                "Mobile number must contain only digits."
            )

        if len(value) != 10:

            raise serializers.ValidationError(
                "Mobile number must be exactly 10 digits."
            )

        if CustomUser.objects.filter(
            mobile_number=value
        ).exists():

            raise serializers.ValidationError(
                "Mobile number already exists."
            )

        return value

    # -------------------------
    # Role validation
    # -------------------------

    def validate_role(self, value):

        allowed_roles = [
            "customer",
            "seller",
            "rider"
        ]

        if value not in allowed_roles:

            raise serializers.ValidationError(
                "Invalid role."
            )

        return value

    # -------------------------
    # Create user
    # -------------------------

    def create(self, validated_data):

        validated_data.pop(
            "confirm_password"
        )

        user = CustomUser.objects.create_user(
            **validated_data
        )

        return user
class Loginserializer(serializers.Serializer):
    email=serializers.CharField()
    password=serializers.CharField()

    class Meta:
        model = CustomUser
        fields = ['username', 'password'] 
     