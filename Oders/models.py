from django.db import models
from django.conf import settings
from Products.models import Products
from Account.models import CustomUser,BuyerShipping
from delivery.models import DeliveryPartner


class AddToCart(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="cart_items")
    product = models.ForeignKey(Products, on_delete=models.CASCADE, related_name="in_carts")
    quantity = models.PositiveIntegerField(default=1) # Fixed lowercase 'quantity'
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'product')

    def __str__(self):
        return f"{self.user.username} - {self.product.name} ({self.quantity})"

    @property
    def total_price(self):
     return round(
        self.product.final_price() * self.quantity,
        2
    )
class Orders(models.Model):
    STATUS = [
        ("pending", "Pending"),
        ("accepted", "Accepted"),
        ("packed", "Packed"),
        ("picked", "Picked Up"),
        ("ontheway", "On The Way"),
        ("delivered", "Delivered"),
        ("cancelled", "Cancelled"),
    ]

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="orders")
    address = models.ForeignKey(BuyerShipping, on_delete=models.PROTECT)
    delivery_partner = models.ForeignKey(
        DeliveryPartner,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    order_id = models.CharField(max_length=50, unique=True)
    status = models.CharField(max_length=30, choices=STATUS, default="pending")

    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    delivery_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)

    payment_method = models.CharField(max_length=30, default="COD") # COD, Razorpay, UPI etc.
    payment_status = models.CharField(max_length=30, default="Pending") # Pending, Paid, Failed
    payment_id = models.CharField(max_length=100, null=True, blank=True) # Payment Gateway Transaction ID

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    delivered_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Order #{self.order_id} - {self.user.username}"


class OrderItem(models.Model):
    order = models.ForeignKey(Orders, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Products, on_delete=models.SET_NULL, null=True)

    # Product Snapshots (Product update hone par order history secure rahegi)
    product_name = models.CharField(max_length=255, null=True, blank=True)
    product_image = models.CharField(max_length=500, null=True, blank=True)
    
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2) # Price at the time of purchase

    @property
    def total_price(self):
        return self.price * self.quantity

    def __str__(self):
        return f"{self.quantity} x {self.product_name or 'Product'} (Order #{self.order.order_id})"