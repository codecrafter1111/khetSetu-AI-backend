from django.db import models
from django.conf import settings
from Oders.models import Orders
from delivery.models import DeliveryPartner

class RiderFeedback(models.Model):

    order = models.OneToOneField(
        Orders,
        on_delete=models.CASCADE,
        related_name="rider_feedback"
    )

    rider = models.ForeignKey(
        DeliveryPartner,
        on_delete=models.CASCADE,
        related_name="feedbacks"
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="rider_feedbacks"
    )

    rating = models.PositiveSmallIntegerField()
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Order {self.order.id} - {self.rating}⭐"