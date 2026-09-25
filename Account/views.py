from django.http.multipartparser import MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView
from .Accountserializer import CustomUserSerializer,Loginserializer

from rest_framework.generics import ListCreateAPIView
from rest_framework import status,permissions
from .models import BuyerShipping,FarmerProfile, FarmDetail, FarmPhoto
from .serializer import FarmerProfileSerializer, FarmDetailSerializer
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import IsAuthenticated

from .tasks import random_otp, send_otp_email,send_wellcome_email,Partner_Join_With_Us
from .otpserializer import OtpSerializer,OtpResendSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from .shippingserializer import BuyerShippingSerializer
from .utils import save_otp
from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser

"""
 Account Registration Login Logout and password reset, Otp verification and resend otp 
"""
class RegisterView(APIView):
    permission_classes = [AllowAny]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    @transaction.atomic
    def post(self, request):
        serializer = CustomUserSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                {
                    "success": False,
                    "errors": serializer.errors
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # Save User & Image
        user = serializer.save()

        # Set Unverified State
        user.is_verified = False
        user.save(update_fields=["is_verified"])

        # Redis OTP Storage
        otp = random_otp()
        save_otp(user.email, otp)

        # Celery Background Email Triggers
        send_otp_email.delay(user.email, str(otp))
        send_wellcome_email.delay(user.email)

        return Response(
            {
                "success": True,
                "message": "User created successfully. OTP sent to email.",
                "data": serializer.data
            },
            status=status.HTTP_201_CREATED
        )


# ---------------------------------------------------------------------
# 2. PROFILE UPDATE VIEW (Existing User Details & Image Update - No OTP)
# ---------------------------------------------------------------------
class UserProfileUpdateView(APIView):
    permission_classes = [IsAuthenticated]  # Login required
    parser_classes = [MultiPartParser, FormParser, JSONParser]  # Form Data & File parser

    def patch(self, request):
        user = request.user  # Logged-in user automatically fetched
        
        serializer = CustomUserSerializer(
            instance=user,
            data=request.data,
            partial=True  # Allows updating selected fields only
        )

        if not serializer.is_valid():
            return Response(
                {
                    "success": False,
                    "errors": serializer.errors
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # Update profile (Calls serializer update method without sending OTP)
        serializer.save()

        return Response(
            {
                "success": True,
                "message": "Profile updated successfully.",
                "data": serializer.data
            },
            status=status.HTTP_200_OK
        )

    def put(self, request):
        return self.patch(request)

    
class Profile(APIView):

    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get(self,request):
        serializer = CustomUserSerializer(request.user)
        return Response(serializer.data)


class OtpView(APIView):

    permission_classes = [AllowAny]
    def post(self, request):
        serializer = OtpSerializer(
            data=request.data
        )
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(
            {
                "message": "OTP verified successfully"
            },
            status=status.HTTP_200_OK
        )


    
class ResendView(APIView):

    permission_classes = [AllowAny]
    def post(self, request):
        serializer = OtpResendSerializer(
            data=request.data
        )
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        user = serializer.user

        otp = random_otp()

        # Save new OTP in Redis
        save_otp(
            user.email,
            otp
        )

        # Send email asynchronously
        send_otp_email.delay(
            user.email,
            str(otp)
        )

        return Response(
            {
                "message": "OTP sent successfully"
            },
            status=status.HTTP_200_OK
        )

    
class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = Loginserializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        email = serializer.validated_data["email"]
        password = serializer.validated_data["password"]

        user = authenticate(
            request=request,
            username=email,
            password=password
        )

        if user is None:
            return Response(
                {"message": "Invalid email or password"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        if not user.is_verified:
            return Response(
                {"message": "User is not verified"},
                status=status.HTTP_403_FORBIDDEN
            )

        refresh = RefreshToken.for_user(user)

        return Response(
            {
                "message": "User logged in successfully",
                "role": user.role,
                "access_token": str(refresh.access_token),
                "refresh_token": str(refresh),
            },
            status=status.HTTP_200_OK
        )  


        
class Logout(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    def post(self,request):
        try:
            refresh_token=request.data["refresh_token"]
            token=RefreshToken(refresh_token)
            token.blacklist()
            return Response({"message":"User logged out successfully"}, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"message":str(e)}, status=status.HTTP_401_UNAUTHORIZED)


"""
shipping address  
"""
class ShippingAddressCreate(APIView):

    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def post(self, request):

        serializer = BuyerShippingSerializer(
            data=request.data,
            context={'request': request}
        )
        print(serializer)

        if serializer.is_valid():
            serializer.save()

            return Response(
                {
                    "message": "Address created successfully"
                },
                status=status.HTTP_201_CREATED
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )
class ShippingAddressList(APIView):

    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get(self, request):
        print(request.user)

        addresses = BuyerShipping.objects.filter(
            user=request.user
        ).order_by(
            '-is_default',
            '-created_at'
        )


        serializer = BuyerShippingSerializer(
            addresses,
            many=True
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )
class SetDefaultAddress(APIView):

    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def post(self, request, id):

        address = BuyerShipping.objects.filter(
            id=id,
            user=request.user
        ).first()

        if not address:
            return Response(
                {"message": "Address not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        address.is_default = True
        address.save()

        return Response(
            {"message": "Default address updated"},
            status=status.HTTP_200_OK
        )

class ShippingAddressUpdate(APIView):

    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def put(self, request, id):

        address = BuyerShipping.objects.filter(
            id=id,
            user=request.user
        ).first()

        if not address:
            return Response(
                {"message": "Address not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = BuyerShippingSerializer(
            address,
            data=request.data,
            partial=True
        )

        if serializer.is_valid():
            serializer.save()

            return Response(
                {
                    "message": "Address updated successfully",
                    "data": serializer.data
                }
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


class ShippingAddressDelete(APIView):

    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def delete(self, request, id):

        address = BuyerShipping.objects.filter(
            id=id,
            user=request.user
        ).first()

        if not address:
            return Response(
                {"message": "Address not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        address.delete()

        return Response(
            {"message": "Address deleted successfully"},
            status=status.HTTP_200_OK
      )
class DefaultAddress(APIView):

    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get(self, request):

        address = BuyerShipping.objects.filter(
            user=request.user,
            is_default=True
        ).first()

        if not address:
            return Response(
                {"message": "No default address found"},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = BuyerShippingSerializer(address)

        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )






# farmer functionality  
# 


class FarmerProfileView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get(self, request):
        profile, _ = FarmerProfile.objects.get_or_create(user=request.user)
        serializer = FarmerProfileSerializer(profile)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        profile, _ = FarmerProfile.objects.get_or_create(user=request.user)
        is_draft = request.data.get("is_draft", True)

        serializer = FarmerProfileSerializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            # Edit karne par agar profile pehle se unverified ho toh re-validation triggers
            serializer.save(is_draft=is_draft)
            return Response(
                {"message": "Farmer profile saved successfully.", "data": serializer.data},
                status=status.HTTP_200_OK,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class FarmDetailView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get(self, request):
        farmer_profile = get_object_or_404(FarmerProfile, user=request.user)
        farm_detail = getattr(farmer_profile, "farm_detail", None)
        if not farm_detail:
            return Response({"detail": "Farm details not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = FarmDetailSerializer(farm_detail)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @transaction.atomic
    def post(self, request):
        farmer_profile, _ = FarmerProfile.objects.get_or_create(user=request.user)
        farm_detail, _ = FarmDetail.objects.get_or_create(farmer_profile=farmer_profile)

        is_draft = request.data.get("is_draft", True)
        uploaded_photos = request.FILES.getlist("uploaded_photos")

        data = request.data.dict() if hasattr(request.data, "dict") else request.data.copy()

        serializer = FarmDetailSerializer(farm_detail, data=data, partial=True)
        if serializer.is_valid():
            saved_farm = serializer.save(is_draft=is_draft)

            if uploaded_photos:
                for photo_file in uploaded_photos[:5]:
                    FarmPhoto.objects.create(farm=saved_farm, image=photo_file)

            return Response(
                {"message": "Farm details saved successfully.", "data": FarmDetailSerializer(saved_farm).data},
                status=status.HTTP_200_OK,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ------------------ ADMIN ONLY VERIFICATION VIEW ------------------
class AdminVerifyFarmerView(APIView):
    """
    Endpoint for Admin / Staff to approve or reject farmer profiles.
    """
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def patch(self, request, profile_id):
        profile = get_object_or_404(FarmerProfile, id=profile_id)
        serializer = AdminVerifyFarmerSerializer(profile, data=request.data, partial=True)

        if serializer.is_valid():
            is_verified = serializer.validated_data.get("is_verified", profile.is_verified)
            
            profile.is_verified = is_verified
            profile.verified_by = request.user
            profile.verified_at = timezone.now() if is_verified else None
            profile.rejection_reason = serializer.validated_data.get(
                "rejection_reason", "" if is_verified else profile.rejection_reason
            )
            profile.save()

            status_msg = "approved & verified" if is_verified else "rejected"
            return Response(
                {
                    "message": f"Farmer profile {status_msg} successfully.",
                    "data": FarmerProfileSerializer(profile).data
                },
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


