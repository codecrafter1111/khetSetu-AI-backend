import uuid

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.utils import timezone
from cloudinary.models import CloudinaryField

from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator

class CustomUser(AbstractUser):
    mobile_number = models.CharField(max_length=15, unique=True, null=True, blank=True)
    is_verified = models.BooleanField(default=False)
    role = models.CharField( choices=[('customer', 'Customer'), ('seller', 'Seller'),('rider', 'Rider'),('admin', 'Admin')], max_length=20, default='customer')
  
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





class FarmerProfile(models.Model):
    class PreferredLanguage(models.TextChoices):
        HINDI = "HI", "Hindi"
        ENGLISH = "EN", "English"
        BENGALI = "BN", "Bengali"
        MARATHI = "MR", "Marathi"
        TELUGU = "TE", "Telugu"
        TAMIL = "TA", "Tamil"
        GUJARATI = "GU", "Gujarati"
        OTHER = "OTHER", "Other"

    class FarmingExperience(models.TextChoices):
        LESS_THAN_1 = "0-1", "0 - 1 year"
        ONE_TO_FIVE = "1-5", "1 - 5 years"
        FIVE_TO_TEN = "5-10", "5 - 10 years"
        TEN_TO_FIFTEEN = "10-15", "10 - 15 years"
        FIFTEEN_PLUS = "15+", "15+ years"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="farmer_profile"
    )
    
    # Personal Info
    full_name = models.CharField(max_length=150)
    mobile_number = models.CharField(
        max_length=15,
        validators=[
            RegexValidator(
                regex=r"^\+?[1-9]\d{1,14}$",
                message="Enter a valid phone number with optional country code.",
            )
        ],
    )
    email_address = models.EmailField(blank=True, null=True)
    preferred_language = models.CharField(
        max_length=10, choices=PreferredLanguage.choices, default=PreferredLanguage.HINDI
    )
    
    # Location
    state = models.CharField(max_length=100)
    district = models.CharField(max_length=100)
    village = models.CharField(max_length=100)
    
    # Experience & Bio
    farming_experience = models.CharField(
        max_length=20, choices=FarmingExperience.choices
    )
    short_bio = models.TextField(max_length=300)

    # Form State
    is_draft = models.BooleanField(default=True)

    # ------------------ ADMIN VERIFICATION FIELDS ------------------
    is_verified = models.BooleanField(
        default=False,
        help_text="Designates whether this farmer profile has been verified by an admin."
    )
    verified_at = models.DateTimeField(blank=True, null=True)
    verified_by = models.ForeignKey(
    settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="verified_farmer_profiles"
    )
    rejection_reason = models.TextField(blank=True, null=True)
    # ---------------------------------------------------------------

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        status_str = "Verified" if self.is_verified else "Pending/Unverified"
        return f"{self.full_name} ({self.mobile_number}) - [{status_str}]"


class FarmDetail(models.Model):
    class AreaUnit(models.TextChoices):
        ACRES = "Acres", "Acres"
        HECTARES = "Hectares", "Hectares"
        BIGHA = "Bigha", "Bigha"

    class SoilType(models.TextChoices):
        LOAMY = "Loamy", "Loamy"
        CLAY = "Clay", "Clay"
        SANDY = "Sandy", "Sandy"
        BLACK = "Black", "Black"
        RED = "Red", "Red"
        ALLUVIAL = "Alluvial", "Alluvial"

    class FarmingMethod(models.TextChoices):
        ORGANIC = "Organic", "Organic"
        CONVENTIONAL = "Conventional", "Conventional"
        NATURAL = "Natural", "Natural"
        PERMACULTURE = "Permaculture", "Permaculture"

    class IrrigationType(models.TextChoices):
        DRIP = "Drip Irrigation", "Drip Irrigation"
        SPRINKLER = "Sprinkler", "Sprinkler"
        FLOOD = "Flood Irrigation", "Flood Irrigation"
        CANAL = "Canal", "Canal"
        RAIN_FED = "Rain-fed", "Rain-fed"

    class WaterSource(models.TextChoices):
        BOREWELL = "Borewell", "Borewell"
        WELL = "Well", "Well"
        CANAL = "Canal", "Canal"
        RIVER = "River", "River"
        POND = "Pond", "Pond"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    farmer_profile = models.OneToOneField(
        FarmerProfile, on_delete=models.CASCADE, related_name="farm_detail"
    )

    # Basic Info
    farm_name = models.CharField(max_length=150)
    farm_owner = models.CharField(max_length=150)
    village = models.CharField(max_length=100)
    district = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    pin_code = models.CharField(
        max_length=10,
        validators=[RegexValidator(regex=r"^\d{6}$", message="Enter a valid 6-digit PIN code.")],
    )

    # Geolocation
    farm_location_address = models.CharField(max_length=255, blank=True, null=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)

    # Land Details
    total_farm_area = models.DecimalField(
        max_digits=8, decimal_places=2, validators=[MinValueValidator(0.01)]
    )
    area_unit = models.CharField(max_length=20, choices=AreaUnit.choices, default=AreaUnit.ACRES)
    soil_type = models.CharField(max_length=30, choices=SoilType.choices)
    farming_method = models.CharField(max_length=30, choices=FarmingMethod.choices)
    irrigation_type = models.CharField(max_length=30, choices=IrrigationType.choices)
    water_source = models.CharField(max_length=30, choices=WaterSource.choices)

    # Main Crops Grown
    main_crops_grown = models.JSONField(default=list)

    # Sustainability Practices
    has_organic_farming = models.BooleanField(default=False)
    has_crop_rotation = models.BooleanField(default=False)
    has_natural_fertilizers = models.BooleanField(default=False)
    has_water_conservation = models.BooleanField(default=False)
    has_soil_health_management = models.BooleanField(default=False)
    has_integrated_pest_management = models.BooleanField(default=False)
    has_agroforestry = models.BooleanField(default=False)
    other_sustainability_practice = models.CharField(max_length=255, blank=True, null=True)

    is_draft = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.farm_name} - {self.farm_owner}"


class FarmPhoto(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    farm = models.ForeignKey(FarmDetail, on_delete=models.CASCADE, related_name="photos")
    image = models.ImageField(upload_to="farm_photos/%Y/%m/")
    uploaded_at = models.DateTimeField(auto_now_add=True)