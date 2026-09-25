import logging
import cloudinary.uploader
from django.db.migrations import serializer
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.core.cache import cache

from rest_framework import generics, status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend

from .models import Categorys, Products, BulkImport, ShopLocation
from feedback.models import ProductRating
from .productserializer import (
    ProductSerializer,
    CategorySerializer,
)
from feedback.serializers import ProductRatingSerializer
from .FramerLocationserial import ShopLocationSerializer
from .services.Productfilters import ProductFilter
from .services.Pagination import ProductPagination
from .tasks import bulk_create_products

logger = logging.getLogger(__name__)


# ----------------------------------------------------------------------
# 1. BULK PRODUCT UPLOAD VIEW
# ----------------------------------------------------------------------
class BulkProductUploadView(APIView):
    """
    Handles CSV file upload for bulk product creation using Celery workers.
    Ensures 'expiry_date' is part of the uploaded data.
    """
    permission_classes = [IsAuthenticated]
    MAX_FILE_SIZE = 20 * 1024 * 1024  # 20 MB

    def post(self, request, *args, **kwargs):
        csv_file = request.FILES.get("file")
        category_id = request.data.get("category_id")

        if not csv_file:
            return Response(
                {"error": "CSV file is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not csv_file.name.lower().endswith(".csv"):
            return Response(
                {"error": "Only valid .csv files are accepted."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if csv_file.size > self.MAX_FILE_SIZE:
            return Response(
                {"error": "File size exceeds maximum allowed limit (20MB)."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            category = Categorys.objects.get(id=category_id)
        except Categorys.DoesNotExist:
            return Response(
                {"error": "Specified Category ID does not exist."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Cloudinary raw upload for CSV
            upload_result = cloudinary.uploader.upload(
                csv_file,
                resource_type="raw",
                folder="swiftcart/csv"
            )

            bulk_import = BulkImport.objects.create(
                uploaded_by=request.user,
                category=category,
                csv_url=upload_result.get("secure_url"),
                cloudinary_public_id=upload_result.get("public_id"),
                status=BulkImport.Status.PENDING
            )

            # Celery asynchronous task kick-off
            task = bulk_create_products.delay(bulk_import.id)
            bulk_import.task_id = task.id
            bulk_import.save(update_fields=["task_id"])

            return Response(
                {
                    "message": "Bulk import process initiated successfully. Ensure CSV contains mandatory 'expiry_date' column.",
                    "import_id": bulk_import.id,
                    "task_id": task.id,
                    "status": bulk_import.status,
                },
                status=status.HTTP_202_ACCEPTED
            )

        except Exception as exc:
            logger.error(f"Bulk product upload failed: {str(exc)}", exc_info=True)
            return Response(
                {"error": "Failed to process bulk upload. Please try again later."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# ----------------------------------------------------------------------
# 2. CATEGORY VIEWS
# ----------------------------------------------------------------------
class CategoryListView(generics.ListAPIView):
    """
    Public listing of all product categories with Redis view caching.
    """
    queryset = Categorys.objects.all().order_by("name")
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]

    @method_decorator(cache_page(60 * 15))  # 15 minutes cache
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)


# ----------------------------------------------------------------------
# 3. PRODUCT CATALOG & DETAIL VIEWS
# ----------------------------------------------------------------------
class ProductListView(generics.ListAPIView):
    """
    Public customer-facing product feed with filtering and pagination.
    Excludes expired products (expiry_date <= current time) dynamically.
    """
    serializer_class = ProductSerializer
    permission_classes = [AllowAny]
    pagination_class = ProductPagination
    filter_backends = [DjangoFilterBackend]
    filterset_class = ProductFilter

    @method_decorator(cache_page(60 * 5))  # 5 minutes cache
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def get_queryset(self):
        # Dynamically exclude expired products using timezone.now()
        return (
            Products.objects
            .select_related("category")
            .filter(is_available=True, expiry_date__gt=timezone.now())
            .order_by("-created_at")
        )


class ProductDetailBySlugView(generics.RetrieveAPIView):
    """
    Retrieve single product details by product Slug.
    """
    serializer_class = ProductSerializer
    permission_classes = [AllowAny]
    lookup_field = "slug"
    lookup_url_kwarg = "Detail_slug"

    def get_queryset(self):
        return (
            Products.objects
            .select_related("category")
            .filter(is_available=True, expiry_date__gt=timezone.now())
        )


# ----------------------------------------------------------------------
# 4. ADMIN / MERCHANT PRODUCT MANAGEMENT VIEWS
# ----------------------------------------------------------------------
class ProductListCreateAdminView(generics.ListCreateAPIView):
     """ Management endpoint to list or create products for back-office. `expiry_date` is validated via ProductSerializer on POST. """
     queryset = Products.objects.select_related("category").all() 
     serializer_class = ProductSerializer
     permission_classes = [IsAuthenticated] 
     def perform_create(self, serializer): 
        """ Automatically assign the currently logged-in user as the owner/creator of the product. """ 
        serializer.save( user=self.request.user )

class ProductDetailAdminView(generics.RetrieveUpdateDestroyAPIView):
    """
    Management endpoint to Retrieve, Update or Soft/Hard delete product by UUID.
    """
    queryset = Products.objects.select_related("category").all()
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = "uuid"


# ----------------------------------------------------------------------
# 5. PRODUCT RATING & REVIEW VIEWS
# ----------------------------------------------------------------------
class ProductRatingCreateView(generics.CreateAPIView):
    """
    Submit rating and review for delivered order items.
    """
    serializer_class = ProductRatingSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ProductRatingListView(generics.ListAPIView):
    """
    List all reviews for a specific product.
    """
    serializer_class = ProductRatingSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        product_uuid = self.kwargs.get("product_uuid")
        return ProductRating.objects.select_related("user", "product").filter(
            product__uuid=product_uuid
        )


# ----------------------------------------------------------------------
# 6. SHOP LOCATION VIEWS
# ----------------------------------------------------------------------
class ShopLocationListCreateView(generics.ListCreateAPIView):
    """
    List or add shop pickup locations for authenticated users.
    """
    serializer_class = ShopLocationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return ShopLocation.objects.filter(user=self.request.user).order_by("name")

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ShopLocationDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or remove shop pickup location.
    """
    serializer_class = ShopLocationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return ShopLocation.objects.filter(user=self.request.user)