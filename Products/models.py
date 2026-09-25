import uuid
from django.db import models
from django.conf import settings
from django.utils.text import slugify
from django.utils import timezone
from cloudinary.models import CloudinaryField


class Categorys(models.Model):
    name = models.CharField(max_length=120, default="all")

    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self):
        return f"{self.name}"


class Products(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE
    )
    category = models.ForeignKey(
        Categorys, 
        on_delete=models.CASCADE, 
        related_name="products"
    )
    name = models.CharField(max_length=200)
    product_key = models.CharField(max_length=300)
    source_url = models.URLField(
        max_length=1000,
        unique=True,
        null=True,
        blank=True
    )

    uuid = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True
    )
    slug = models.SlugField(
        unique=True,
        blank=True,
        max_length=200,
    )

    brand = models.CharField(max_length=100)
    image = CloudinaryField("image", folder="products/images")
    stock = models.PositiveIntegerField(default=30)

    package_quantity = models.DecimalField(max_digits=10, decimal_places=2)
    package_unit = models.CharField(max_length=20)

    price_inr = models.DecimalField(max_digits=10, decimal_places=2)
    offer = models.DecimalField(max_digits=5, decimal_places=2, default=17)

    # ── MANDATORY EXPIRY FIELD FOR FARMING PRODUCE ──────────────────────
    expiry_date = models.DateTimeField(
        help_text="Mandatory expiry date for fresh farm produce"
    )

    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def is_expired(self):
        """Check if product has passed its expiry date"""
        if self.expiry_date:
            return timezone.now() >= self.expiry_date
        return True

    def final_price(self):
        return self.price_inr - (
            self.price_inr * self.offer / 100
        )

    def offer_price(self):
        return self.price_inr - self.final_price()

    def __str__(self):
        return f"{self.name} - {self.brand}"

    def save(self, *args, **kwargs):
        # 1. Automatic availability toggle based on expiry and stock
        if self.is_expired or self.stock <= 0:
            self.is_available = False
        else:
            self.is_available = True

        # 2. Unique Slug generation logic
        if not self.slug:
            base_slug = slugify(self.name)
            new_slug = base_slug
            counter = 1

            while Products.objects.filter(
                slug=new_slug
            ).exclude(pk=self.pk).exists():
                new_slug = f"{base_slug}-{counter}"
                counter += 1

            self.slug = new_slug

        # 3. Save instance
        super().save(*args, **kwargs)


class ShopLocation(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE
    )
    name = models.CharField(max_length=200)
    address = models.TextField()
    latitude = models.DecimalField(max_digits=10, decimal_places=8)
    longitude = models.DecimalField(max_digits=11, decimal_places=8)

    def __str__(self):
        return self.name


class BulkImport(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PROCESSING = "processing", "Processing"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"

    uuid = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False
    )
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="bulk_imports"
    )
    category = models.ForeignKey(
        Categorys,
        on_delete=models.PROTECT,
        related_name="bulk_imports"
    )
    csv_url = models.URLField(max_length=2000)
    cloudinary_public_id = models.CharField(max_length=500, blank=True)
    task_id = models.CharField(max_length=255, blank=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )
    total_rows = models.PositiveIntegerField(default=0)
    created_count = models.PositiveIntegerField(default=0)
    skipped_count = models.PositiveIntegerField(default=0)
    failed_count = models.PositiveIntegerField(default=0)
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Import {self.id} - {self.status}"