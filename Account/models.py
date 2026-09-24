from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.utils import timezone
from cloudinary.models import CloudinaryField

class CustomUser(AbstractUser):
    mobile_number = models.CharField(max_length=15, unique=True, null=True, blank=True)
    is_verified = models.BooleanField(default=False)
    role = models.CharField( choices=[('customer', 'Customer'), ('seller', 'Seller'),('rider', 'Rider')])
  
    profile_image = CloudinaryField("profile_image", folder ="Account/Profile",blank=True)
    email = models.EmailField(unique=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.email



class BuyerShipping(models.Model):

    ADDRESS_TYPE = (
        ('home', 'Home'),
        ('work', 'Work'),
        ('other', 'Other'),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='addresses'
    )

    full_name = models.CharField(max_length=100)
    mobile_number = models.CharField(max_length=15)

    address_line = models.CharField(max_length=255)
    landmark = models.CharField(max_length=255, blank=True, null=True)
    opposite_of = models.CharField(max_length=255, blank=True, null=True)

    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    zip_code = models.CharField(max_length=10)

    address_type = models.CharField(max_length=10, choices=ADDRESS_TYPE, default='home')
    latitude = models.DecimalField(max_digits=10, decimal_places=8, null=True, blank=True)
    longitude = models.DecimalField(max_digits=11, decimal_places=8, null=True, blank=True)

    is_default = models.BooleanField(default=False)   # ⭐ important

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.full_name} - {self.city}"

    """
    Note : 
    Address ko related_name 'addresses' me store karega
    And .exclude(id=self.id) → iska matlab hai ki jo user login hoga uski id add nhi krni hai baaki sabhi  old address ko false krdo
    """


    def save(self,*args,**kwargs):
        if self.is_default:
            BuyerShipping.objects.filter(
                user=self.user,
                is_default=True
            ).exclude(id=self.id).update(is_default=False)
        super().save(*args,**kwargs)