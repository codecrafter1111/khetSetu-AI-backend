from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import permission_classes
from .models import DeliveryPartner, PartnerDocuments, PartnerLocation, DeliveryAssignment, RiderEarning
from .serializer import (
    PartnerDocumentsSerializer,
    PartnerLocationSerializer,
    DeliveryPartnerSerializer,
    DeliveryAssignmentSerializer,
    RiderEarningSerializer
)
from Account.models import CustomUser
from Oders.models import OrderItem, Orders
from decimal import Decimal
import math
from Oders.serializers import CheckoutSerializer
from rest_framework.generics import CreateAPIView, RetrieveAPIView
from rest_framework import generics
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework_simplejwt.authentication import JWTAuthentication
from .utils import generate_partner_id
from Account.tasks import Partner_Join_With_Us
from .serializer import RiderActiveOrderSerializer,CustomerTrackingSerializer
from rest_framework.generics import GenericAPIView


# show user activae order for joining room 
class RiderActiveOrderView(GenericAPIView):
    serializer_class = RiderActiveOrderSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request):
        order = (
            Orders.objects
            .select_related("address", "delivery_partner")
            .filter(
                delivery_partner=request.user.delivery_partner,
                status__in=[
                    "accepted",
                    "packed",
                    "picked",
                    "ontheway"
                ]
            )
            .order_by("-created_at")
            .first()
        )

        if not order:
            return Response({
                "active_order": False,
                "message": "No active order found"
            })

        serializer = self.get_serializer(order)

        return Response({
            "active_order": True,
            "order": serializer.data
        })

class CustomerTrackingView(RetrieveAPIView):

    serializer_class = CustomerTrackingSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = "order_id"

    def get_queryset(self):
        return (
            Orders.objects
            .select_related(
                "delivery_partner",
                "live_location"
            )
            .filter(user=self.request.user)
        )
    
class DeliveryPartnerProfileView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]  # Add your authentication classes here
    parser_classes = [MultiPartParser, FormParser]  # Image upload handle karne ke liye

    def get(self, request):
        """Current logged-in rider ka dashboard data fetch karein."""
        partner = get_object_or_404(DeliveryPartner, user=request.user)
        serializer = DeliveryPartnerSerializer(partner)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request):
        """Rider profile details partial update karein."""
        partner = get_object_or_404(DeliveryPartner, user=request.user)
        serializer = DeliveryPartnerSerializer(partner, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class DeliveryPartnerRegistrationView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        user = request.user
        if hasattr(user, 'delivery_partner'):
            return Response({"message": "You are already registered as a delivery partner."}, status=status.HTTP_400_BAD_REQUEST)

        # Generate unique Partner ID
        partner_id = generate_partner_id()
        Partner_Join_With_Us.delay(user.email, partner_id)  # Celery task to send email easily
    
        serializer = DeliveryPartnerSerializer(data= request.data)
        if serializer.is_valid():
            serializer.save(user=user, Partner_id=partner_id)
            return Response({
                "message": "Delivery partner registered successfully.",
                "data": serializer.data
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ToggleOnlineStatusView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def post(self, request):
        """Rider ko Online/Offline aur Availability set karne ke liye."""
        partner = get_object_or_404(DeliveryPartner, user=request.user)
        
        is_online = request.data.get("is_online", not partner.is_online)
        partner.is_online = is_online
        
        # Agar rider offline jaye toh unavailable automatically set ho jaye
        if not is_online:
            partner.is_available = False
        else:
            partner.is_available = request.data.get("is_available", True)

        partner.save()

        return Response({
            "message": "Status updated successfully.",
            "is_online": partner.is_online,
            "is_available": partner.is_available
        }, status=status.HTTP_200_OK)   
    
# 2. Partner Document Upload & Verification here
# ---------------------------------------------------------------------
class PartnerDocumentUploadView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    parser_classes = [MultiPartParser, FormParser] 

    def get(self, request):
        """Uploaded documents ka status check karein."""
        partner = get_object_or_404(DeliveryPartner, user=request.user)
        documents = getattr(partner, 'partner_document', None)
        if not documents:
            return Response({"message": "No documents uploaded yet."}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = PartnerDocumentsSerializer(documents)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        """Documents upload ya update (DL, RC, Aadhar) karein."""
        partner = get_object_or_404(DeliveryPartner, user=request.user)
        documents, created = PartnerDocuments.objects.get_or_create(partner=partner)

        serializer = PartnerDocumentsSerializer(documents, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({
                "message": "Documents uploaded successfully.",
                "data": serializer.data
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# delivery partner store live location update for calculation of distance and delivery assignment
class PartnerLocationUpdateView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def post(self, request):
        """Rider ke current location ko update karein."""
        partner = get_object_or_404(DeliveryPartner, user=request.user)
        latitude = request.data.get("latitude")
        longitude = request.data.get("longitude")

        if latitude is None or longitude is None:
            return Response(
                {"error": "Both latitude and longitude are required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        location_obj, created = PartnerLocation.objects.update_or_create(
            rider=partner,
            defaults={"latitude": latitude, "longitude": longitude}
        )

        serializer = PartnerLocationSerializer(location_obj)
        return Response({
            "message": "Location updated successfully.",
            "data": serializer.data
        }, status=status.HTTP_200_OK)



class CheckoutOrderView(CreateAPIView):
    serializer_class = CheckoutSerializer
    permission_classes = [IsAuthenticated]

    # -------------------------------------------------
    # Haversine Distance (KM)
    # -------------------------------------------------
    def calculate_distance(self, lat1, lon1, lat2, lon2):

        R = 6371

        lat1 = math.radians(float(lat1))
        lon1 = math.radians(float(lon1))
        lat2 = math.radians(float(lat2))
        lon2 = math.radians(float(lon2))

        dlat = lat2 - lat1
        dlon = lon2 - lon1

        a = (
            math.sin(dlat / 2) ** 2 +
            math.cos(lat1) *
            math.cos(lat2) *
            math.sin(dlon / 2) ** 2
        )

        c = 2 * math.atan2(
            math.sqrt(a),
            math.sqrt(1 - a)
        )

        return round(R * c, 2)

    # -------------------------------------------------
    # Find nearest rider
    # -------------------------------------------------
    def get_nearest_rider(self, address):

        nearest_rider = None
        shortest_distance = float("inf")

        locations = (
            PartnerLocation.objects
            .select_related("rider")
            .filter(rider__is_available=True)
        )

        for location in locations:

            distance = self.calculate_distance(
                address.latitude,
                address.longitude,
                location.latitude,
                location.longitude
            )

            if distance < shortest_distance:
                shortest_distance = distance
                nearest_rider = location.rider

        return nearest_rider, shortest_distance

    # -------------------------------------------------
    # Checkout
    # -------------------------------------------------
    @transaction.atomic
    def create(self, request, *args, **kwargs):

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        cart_items = (
            AddToCart.objects
            .select_related("product")
            .filter(user=request.user)
        )

        if not cart_items.exists():
            return Response(
                {"message": "Cart is empty"},
                status=400
            )

        address = get_object_or_404(
            BuyerShipping,
            id=serializer.validated_data["address_id"],
            user=request.user
        )

        # ---------------- Bill ----------------

        subtotal = Decimal("0.00")

        for item in cart_items:
            subtotal += Decimal(str(item.total_price))

        delivery_fee = Decimal("40.00")
        total_amount = subtotal + delivery_fee

        # ---------------- Order ----------------

        order = Orders.objects.create(
            user=request.user,
            address=address,
            order_id=f"KS{uuid.uuid4().hex[:8].upper()}",
            subtotal=subtotal,
            delivery_fee=delivery_fee,
            total_amount=total_amount,
            payment_method=serializer.validated_data["payment_method"],
            payment_status="Pending",
            status="pending"
        )

        # ---------------- Order Items ----------------

        order_items = []

        for item in cart_items:

            order_items.append(
                OrderItem(
                    order=order,
                    product=item.product,
                    product_name=item.product.name,
                    product_image=item.product.pr_small_url,
                    quantity=item.quantity,
                    price=item.product.final_price()
                )
            )

        OrderItem.objects.bulk_create(order_items)

        # ---------------- Rider Assignment ----------------

        rider, distance = self.get_nearest_rider(address)

        if rider:

            order.delivery_partner = rider
            order.status = "accepted"
            order.save(
                update_fields=[
                    "delivery_partner",
                    "status"
                ]
            )

            rider.is_available = False
            rider.save(update_fields=["is_available"])

            # Assignment
            DeliveryAssignment.objects.create(
                order=order,
                rider=rider,
                status="assigned"
            )

            # ₹10 per KM
            earning = Decimal(str(distance)) * Decimal("10")

            RiderEarning.objects.create(
                rider=rider,
                order=order,
                delivery_fee=earning,
                tip=Decimal("0.00")
            )

        # ---------------- Clear Cart ----------------

        cart_items.delete()

        return Response(
            {
                "message": "Order placed successfully",
                "order_id": order.order_id,
                "status": order.status,
                "assigned_rider": rider.fullName if rider else None,
                "distance_km": distance if rider else None,
                "rider_earning": float(earning) if rider else 0,
                "total_amount": order.total_amount
            },
            status=status.HTTP_201_CREATED
        )