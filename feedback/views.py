from django.db import transaction
from django.shortcuts import get_object_or_404

from rest_framework import status
from rest_framework.generics import CreateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError

from Oders.models import Orders
from .models import ProductRating, RiderFeedback
from .serializers import ProductRatingSerializer, RiderFeedbackSerializer, RiderReviewSerializer
from django.db.models import Avg
from rest_framework.views import APIView
from rest_framework import viewsets, permissions
from rest_framework.decorators import action


class RiderFeedbackCreateView(CreateAPIView):
    serializer_class = RiderFeedbackSerializer
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def create(self, request, *args, **kwargs):

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        order = get_object_or_404(
            Orders.objects.select_related("delivery_partner"),
            id=request.data.get("order")
        )

        # Only order owner
        if order.user != request.user:
            raise ValidationError(
                "You are not allowed to review this order."
            )

        # Delivered only
        if order.status != "delivered":
            raise ValidationError(
                "Feedback can only be given after delivery."
            )

        # Rider assigned
        if not order.delivery_partner:
            raise ValidationError(
                "No delivery partner assigned."
            )

        # Prevent duplicate feedback
        if RiderFeedback.objects.filter(order=order).exists():
            raise ValidationError(
                "Feedback already submitted."
            )

        feedback = serializer.save(
            user=request.user,
            order=order,
            rider=order.delivery_partner
        )

        return Response(
            {
                "message": "Thank you for your feedback!",
                "feedback": RiderFeedbackSerializer(feedback).data
            },
            status=status.HTTP_201_CREATED
        )

class RiderDashboardView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        rider = request.user.delivery_partner

        reviews = RiderFeedback.objects.filter(
            rider=rider
        ).select_related("user").order_by("-created_at")

        stats = reviews.aggregate(
            average_rating=Avg("rating")
        )

        return Response({
            "rider_name": rider.fullName,
            "average_rating": round(
                stats["average_rating"] or 0,
                1
            ),
            "total_reviews": reviews.count(),
            "recent_reviews": RiderReviewSerializer(
                reviews[:5],
                many=True
            ).data
        })    



class ProductRatingViewSet(viewsets.ModelViewSet):
    queryset = ProductRating.objects.all()
    serializer_class = ProductRatingSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        queryset = super().get_queryset()
        product_id = self.request.query_params.get("product_id")
        
        # Public product reviews filter by product ID
        if product_id:
            return queryset.filter(product_id=product_id)
            
        # Authenticated customer view own ratings
        if self.action in ["list", "my_ratings"] and self.request.user.is_authenticated:
            return queryset.filter(user=self.request.user)
            
        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=["get"], permission_classes=[permissions.IsAuthenticated])
    def my_ratings(self, request):
        """ Get all product ratings submitted by current logged-in customer """
        ratings = ProductRating.objects.filter(user=request.user)
        serializer = self.get_serializer(ratings, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)    