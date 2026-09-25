import re
from rest_framework import serializers
from .models import CustomUser
from Products.services.cloudnary_images import get_pr_small_url


class CustomUserSerializer(serializers.ModelSerializer):

    confirm_password = serializers.CharField(
        write_only=True, required=False, allow_blank=True
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
            "password": {"write_only": True, "required": False, "allow_blank": True},
            "email": {"required": False},
            "username": {"required": False},
            "mobile_number": {"required": False},
            "role": {"required": False},
        }

    # -------------------------
    # Helper / Serializer Method
    # -------------------------
    def get_pr_small_url(self, obj):
        try:
            if obj.profile_image and hasattr(obj.profile_image, "public_id"):
                return get_pr_small_url(obj.profile_image.public_id)
            elif obj.profile_image:
                return get_pr_small_url(str(obj.profile_image))
        except Exception:
            pass
        return None

    # -------------------------
    # Object-level Validation
    # -------------------------
    def validate(self, attrs):
        password = attrs.get("password")
        confirm_password = attrs.get("confirm_password")

        # Registration Flow: Passwords are required
        if not self.instance:
            if not password:
                raise serializers.ValidationError({"password": "Password is required."})
            if not confirm_password:
                raise serializers.ValidationError({"confirm_password": "Confirm password is required."})

        # Check Password Matching if updated or registering
        if password or confirm_password:
            if password != confirm_password:
                raise serializers.ValidationError({
                    "confirm_password": "Passwords do not match."
                })

        return attrs

    # -------------------------
    # Email Validation
    # -------------------------
    def validate_email(self, value):
        if not value:
            return value

        value = value.lower().strip()

        # Update case: Current user record ignore karo
        query = CustomUser.objects.filter(email__iexact=value)
        if self.instance:
            query = query.exclude(pk=self.instance.pk)

        if query.exists():
            raise serializers.ValidationError("Email already exists.")

        if not value.endswith("@gmail.com"):
            raise serializers.ValidationError("Email must be a Gmail address.")

        return value

    # -------------------------
    # Username Validation
    # -------------------------
    def validate_username(self, value):
        if not value:
            return value

        value = value.strip()

        if len(value) < 3:
            raise serializers.ValidationError("Username must be at least 3 characters long.")

        if not re.match(r"^[a-zA-Z0-9_]+$", value):
            raise serializers.ValidationError("Username can contain only letters, numbers and underscores.")

        query = CustomUser.objects.filter(username__iexact=value)
        if self.instance:
            query = query.exclude(pk=self.instance.pk)

        if query.exists():
            raise serializers.ValidationError("Username already exists.")

        return value

    # -------------------------
    # Password Validation
    # -------------------------
    def validate_password(self, value):
        if value and len(value) < 6:
            raise serializers.ValidationError("Password must be at least 6 characters long.")
        return value

    # -------------------------
    # Mobile Number Validation
    # -------------------------
    def validate_mobile_number(self, value):
        if not value:
            return value

        value = str(value).strip()

        if not value.isdigit():
            raise serializers.ValidationError("Mobile number must contain only digits.")

        if len(value) != 10:
            raise serializers.ValidationError("Mobile number must be exactly 10 digits.")

        query = CustomUser.objects.filter(mobile_number=value)
        if self.instance:
            query = query.exclude(pk=self.instance.pk)

        if query.exists():
            raise serializers.ValidationError("Mobile number already exists.")

        return value

    # -------------------------
    # Role Validation
    # -------------------------
    def validate_role(self, value):
        allowed_roles = ["customer", "seller", "rider", "admin"]
        if value and value not in allowed_roles:
            raise serializers.ValidationError("Invalid role.")
        return value

    # -------------------------
    # User Creation (POST)
    # -------------------------
    def create(self, validated_data):
        validated_data.pop("confirm_password", None)
        user = CustomUser.objects.create_user(**validated_data)
        return user

    # -------------------------
    # User Update (PATCH / PUT)
    # -------------------------
    def update(self, instance, validated_data):
        validated_data.pop("confirm_password", None)
        password = validated_data.pop("password", None)

        # Normal Fields Update (including profile_image)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        # Password Update Handle
        if password:
            instance.set_password(password)

        instance.save()
        return instance
class Loginserializer(serializers.Serializer):
    email=serializers.CharField()
    password=serializers.CharField()

    class Meta:
        model = CustomUser
        fields = ['username', 'password'] 
     