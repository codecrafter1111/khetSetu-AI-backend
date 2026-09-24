import math
from Products.services.cloudnary_images import get_pr_small_url
from rest_framework.views import APIView
import uuid
from decimal import Decimal
from rest_framework.generics import CreateAPIView
from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework import status, permissions
from django.shortcuts import get_object_or_404
from .models import AddToCart, Products
from .CartSerializer import CartItemSerializer, AddToCartSerializer
from rest_framework.permissions import IsAuthenticated
from Account.models import BuyerShipping
from delivery.models import DeliveryPartner, PartnerLocation
from .models import Orders, OrderItem
from .serializers import CheckoutSerializer
from .serializers import CheckoutSerializer
from delivery.models import PartnerLocation, DeliveryAssignment, RiderEarning

class CartView(APIView):

    permission_classes = [permissions.IsAuthenticated]

    # 1. GET: Fetch User Cart Items & Grand Total
    def get(self, request):
        cart_items = AddToCart.objects.filter(user=request.user).select_related('product')
        serializer = CartItemSerializer(cart_items, many=True)

        grand_total = sum(item.total_price for item in cart_items)

        return Response({
            "success": True,
            "cart_count": cart_items.count(),
            "grand_total": round(grand_total, 2),
            "items": serializer.data
        }, status=status.HTTP_200_OK)

    # 2. POST: Add Product to Cart / Increment Quantity
    def post(self, request):
        serializer = AddToCartSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        product_id = serializer.validated_data['product_id']  # this is now a UUID
        quantity = serializer.validated_data['quantity']

        # CHANGED: lookup by uuid, not internal integer id —
        # matches what the frontend actually has access to.
        product = get_object_or_404(Products, uuid=product_id)

        if not product.is_available or product.stock <= 0:
            return Response({"error": "This product is currently out of stock."}, status=status.HTTP_400_BAD_REQUEST)

        cart_item, created = AddToCart.objects.get_or_create(
            user=request.user,
            product=product,
            defaults={'quantity': quantity}
        )

        if not created:
            if cart_item.quantity + quantity > product.stock:
                return Response({
                    "error": f"Cannot add more. Stock limit is {product.stock} items."
                }, status=status.HTTP_400_BAD_REQUEST)

            cart_item.quantity += quantity
            cart_item.save()

        return Response({
            "message": "Product added to cart successfully!",
            "data": CartItemSerializer(cart_item).data
        }, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)

    # 3. PATCH: Update Item Quantity Direct (e.g., set quantity = 3)
    def patch(self, request):
        cart_id = request.data.get('cart_id')
        new_quantity = request.data.get('quantity')

        if not cart_id or new_quantity is None:
            return Response({"error": "cart_id and quantity are required."}, status=status.HTTP_400_BAD_REQUEST)

        cart_item = get_object_or_404(AddToCart, id=cart_id, user=request.user)

        if int(new_quantity) <= 0:
            cart_item.delete()
            return Response({"message": "Item removed from cart."}, status=status.HTTP_200_OK)

        if int(new_quantity) > cart_item.product.stock:
            return Response({
                "error": f"Only {cart_item.product.stock} items available in stock."
            }, status=status.HTTP_400_BAD_REQUEST)

        cart_item.quantity = new_quantity
        cart_item.save()

        return Response({
            "message": "Cart updated.",
            "data": CartItemSerializer(cart_item).data
        }, status=status.HTTP_200_OK)

    # 4. DELETE: Remove Item from Cart
    def delete(self, request):
        cart_id = request.data.get('cart_id')
        clear_all = request.data.get('clear_all', False)

        if clear_all:
            AddToCart.objects.filter(user=request.user).delete()
            return Response({"message": "Cart cleared successfully!"}, status=status.HTTP_200_OK)

        if not cart_id:
            return Response({"error": "cart_id is required."}, status=status.HTTP_400_BAD_REQUEST)

        cart_item = get_object_or_404(AddToCart, id=cart_id, user=request.user)
        cart_item.delete()

        return Response({"message": "Item removed from cart successfully!"}, status=status.HTTP_200_OK)




class CheckoutOrderView(CreateAPIView):
    serializer_class = CheckoutSerializer
    permission_classes = [IsAuthenticated]

    # --------------------------------------------------
    # Haversine Formula (Nearest Rider)
    # --------------------------------------------------
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

    # --------------------------------------------------
    # Find nearest available rider
    # --------------------------------------------------
    def get_nearest_rider(self, address):

        nearest_rider = None
        shortest_distance = float("inf")

        rider_locations = (
            PartnerLocation.objects
            .select_related("rider")
            .filter(rider__is_available=True)
        )

        for location in rider_locations:

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

    # --------------------------------------------------
    # Checkout API
    # --------------------------------------------------
    @transaction.atomic
    def create(self, request, *args, **kwargs):

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # ---------------- CART ----------------

        cart_items = (
            AddToCart.objects
            .select_related("product")
            .filter(user=request.user)
        )

        if not cart_items.exists():
            return Response(
                {"message": "Cart is empty"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # ---------------- ADDRESS ----------------

        address = get_object_or_404(
            BuyerShipping,
            id=serializer.validated_data["address_id"],
            user=request.user
        )

        # ---------------- BILL ----------------

        subtotal = Decimal("0.00")

        for item in cart_items:
            subtotal += Decimal(str(item.total_price))

        delivery_fee = Decimal("40.00")
        total_amount = subtotal + delivery_fee

        # ---------------- CREATE ORDER ----------------

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

        # ---------------- ORDER ITEMS ----------------

        order_items = []

        for item in cart_items:

            image_url = ""

            if item.product.image:
                image_url = get_pr_small_url(
                    item.product.image.public_id
                )

            order_items.append(
                OrderItem(
                    order=order,
                    product=item.product,
                    product_name=item.product.name,
                    product_image=image_url,
                    quantity=item.quantity,
                    price=Decimal(str(item.product.final_price()))
                )
            )

        OrderItem.objects.bulk_create(order_items)

        # ---------------- ASSIGN RIDER ----------------

        rider, distance = self.get_nearest_rider(address)

        earning = Decimal("0.00")

        if rider:

            order.delivery_partner = rider
            order.status = "accepted"

            order.save(
                update_fields=[
                    "delivery_partner",
                    "status"
                ]
            )

            # Rider unavailable
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

        # ---------------- CLEAR CART ----------------

        cart_items.delete()

        return Response(
            {
                "message": "Order placed successfully",
                "order_id": order.order_id,
                "status": order.status,
                "assigned_rider": rider.fullName if rider else None,
                "distance_km": distance if rider else None,
                "rider_earning": float(earning),
                "total_amount": float(order.total_amount)
            },
            status=status.HTTP_201_CREATED
        )