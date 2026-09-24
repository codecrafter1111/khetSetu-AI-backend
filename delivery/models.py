from django.db import models
from django.conf import settings
from cloudinary.models import CloudinaryField


class DeliveryPartner(models.Model):

    VEHICLE_CHOICES = [
        ("bike", "Bike"),
        ("scooter", "Scooter"),
        ("cycle", "Cycle"),
    ]

    user = models.OneToOneField(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,related_name="delivery_partner")
    Partner_id = models.CharField(max_length=20,unique=True)

    profile_image = CloudinaryField("profile_image",folder="Partner/Profile")
    fullName = models.CharField(max_length=100)

    mobile = models.CharField(max_length=12,unique=True)
    Vehicle_type = models.CharField(choices=VEHICLE_CHOICES,max_length=20)
    Vehicle_number = models.CharField(max_length=12,unique=True)

    is_online = models.BooleanField(default=False)
    is_available = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False)

    rating = models.FloatField(default=0)
    total_deliveries = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.fullName} - {self.Vehicle_number}"


# Partner ke documents
class PartnerDocuments(models.Model):

    partner = models.OneToOneField(DeliveryPartner,on_delete=models.CASCADE,related_name="partner_document")
    Driving_licens = CloudinaryField("Driving_licens",folder="partnerDocuments/")

    Vehicle_Rc = CloudinaryField("Vehicle_Rc",folder="partnerDocuments/")
    Aadhar_docs = CloudinaryField("Aadhar_docs", folder="partnerDocuments/")

    verified = models.BooleanField(default=False)


# Partner location for tracking
class PartnerLocation(models.Model):

    rider = models.OneToOneField(DeliveryPartner, on_delete=models.CASCADE,related_name="delivery_partner")
    latitude = models.DecimalField(max_digits=9,decimal_places=6)
    longitude = models.DecimalField(max_digits=9,decimal_places=6)

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.rider.fullName} Location"


# Delivery assignment
class DeliveryAssignment(models.Model):

    STATUS_CHOICES = [
        ("assigned", "Assigned"),
        ("picked", "Picked Up"),
        ("on_the_way", "On The Way"),
        ("delivered", "Delivered"),
    ]

    order = models.OneToOneField("Oders.Orders",on_delete=models.CASCADE,related_name="delivery_assignment")

    rider = models.ForeignKey(DeliveryPartner,on_delete=models.CASCADE,related_name="assignments")

    status = models.CharField(max_length=30,choices=STATUS_CHOICES,default="assigned")

    assigned_at = models.DateTimeField(auto_now_add=True)

    delivered_at = models.DateTimeField(null=True,blank=True)

    def __str__(self):
        return f"{self.order} - {self.rider.fullName}"


# Rider earnings
class RiderEarning(models.Model):

    rider = models.ForeignKey( DeliveryPartner,on_delete=models.CASCADE,related_name="earnings")

    order = models.OneToOneField("Oders.Orders", on_delete=models.CASCADE, related_name="rider_earning")
    delivery_fee = models.DecimalField(max_digits=8,decimal_places=2)
    tip = models.DecimalField(max_digits=8, decimal_places=2,default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.rider.fullName} - {self.delivery_fee}"