from .models import  CustomUser
from rest_framework import serializers
from .tasks import random_otp, send_otp_email
from django.utils import timezone
from .utils import get_otp_key,get_otp_ttl,get_otp,delete_otp


class OtpSerializer(serializers.Serializer):

    email = serializers.EmailField()

    otp = serializers.CharField(
        max_length=6
    )

    def validate(self, attrs):

        email = attrs["email"].lower()
        otp = attrs["otp"]

        try:
            user = CustomUser.objects.get(
                email__iexact=email
            )

        except CustomUser.DoesNotExist:

            raise serializers.ValidationError(
                {
                    "email": "User not found."
                }
            )

        if user.is_verified:

            raise serializers.ValidationError(
                {
                    "otp": "User is already verified."
                }
            )

        stored_otp = get_otp(email)

        if stored_otp is None:

            raise serializers.ValidationError(
                {
                    "otp": "OTP expired or not found."
                }
            )

        if str(stored_otp) != str(otp):

            raise serializers.ValidationError(
                {
                    "otp": "Invalid OTP."
                }
            )

        # OTP correct
        user.is_verified = True

        user.save(
            update_fields=["is_verified"]
        )

        # OTP cannot be reused
        delete_otp(email)

        attrs["user"] = user

        return attrs
    
class OtpResendSerializer(serializers.Serializer):

    email = serializers.EmailField()

    def validate_email(self, value):

        email = value.lower()

        try:

            user = CustomUser.objects.get(
                email__iexact=email
            )

        except CustomUser.DoesNotExist:

            raise serializers.ValidationError(
                "User not found."
            )

        if user.is_verified:

            raise serializers.ValidationError(
                "User is already verified."
            )

        existing_otp = get_otp(email)

        if existing_otp is not None:

            ttl = get_otp_ttl(email)

            raise serializers.ValidationError(
                f"Please wait {ttl} seconds before requesting another OTP."
            )

        self.user = user

        return email