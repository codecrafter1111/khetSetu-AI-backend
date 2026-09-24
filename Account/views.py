from rest_framework.response import Response
from rest_framework.views import APIView
from .Accountserializer import CustomUserSerializer,Loginserializer

from rest_framework.generics import ListCreateAPIView
from rest_framework import status
from .models import BuyerShipping

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

"""
 Account Registration Login Logout and password reset, Otp verification and resend otp 
"""
class RegisterView(APIView):

    permission_classes = [AllowAny]

    def post(self, request):
      
        serializer = CustomUserSerializer(
            data=request.data
        )

        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        user = serializer.save()
        otp = random_otp()
        # Redis
        save_otp(
            user.email,
            otp
        )
        # Celery
        send_otp_email.delay(
            user.email,
            str(otp)
        )
        send_wellcome_email.delay(
            user.email
        )

        user.is_verified = False
        user.save(update_fields=["is_verified"])

        return Response(
            {
                "message": "User created successfully"
            },
            status=status.HTTP_201_CREATED
        )
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