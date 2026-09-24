from django.db import models
from Oders.models import Orders

class RiderLocation(models.Model):
    order = models.OneToOneField(
        Orders,
        on_delete=models.CASCADE,
        related_name="live_location"
    )

    latitude = models.DecimalField(max_digits=10, decimal_places=7)
    longitude = models.DecimalField(max_digits=10, decimal_places=7)

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.order.order_id