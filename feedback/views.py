from django.db import transaction
from django.shortcuts import get_object_or_404

from rest_framework import status
from rest_framework.generics import CreateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError

from Oders.models import Orders
from .models import RiderFeedback
from .serializers import RiderFeedbackSerializer, RiderReviewSerializer
from django.db.models import Avg
from rest_framework.views import APIView


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