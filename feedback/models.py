from django.db import models
from django.conf import settings
from Oders.models import Orders
from delivery.models import DeliveryPartner
from django.core.validators import MinValueValidator, MaxValueValidator
from Products.models import Products

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

class ProductRating(models.Model):
    order = models.ForeignKey(
        Orders,
        on_delete=models.CASCADE,
        related_name="product_ratings"
    )
    product = models.ForeignKey(
        Products,
        on_delete=models.CASCADE,
        related_name="ratings"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="product_ratings"
    )
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    review = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        # Ek order me ek product ko user ek hi baar review kar sake
        unique_together = ('order', 'product', 'user')

    def __str__(self):
        return f"{self.product.name} - {self.rating}⭐ by {self.user.email}"        