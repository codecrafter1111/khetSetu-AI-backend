from django.urls import path
from . import views

urlpatterns = [
    # ------------------------------------------------------------------
    # 1. CATEGORIES
    # ------------------------------------------------------------------
    path(
        "categories/",
        views.CategoryListView.as_view(),
        name="category-list"
    ),

    # ------------------------------------------------------------------
    # 2. BULK UPLOAD
    # ------------------------------------------------------------------
    path(
        "products/bulk-upload/",
        views.BulkProductUploadView.as_view(),
        name="product-bulk-upload"
    ),

    # ------------------------------------------------------------------
    # 3. PUBLIC PRODUCT CATALOG & DETAIL
    # ------------------------------------------------------------------
    path(
        "products/",
        views.ProductListView.as_view(),
        name="product-list"
    ),
    path(
        "products/detail/<slug:Detail_slug>/",
        views.ProductDetailBySlugView.as_view(),
        name="product-detail-slug"
    ),

    # ------------------------------------------------------------------
    # 4. PRODUCT REVIEWS & RATINGS
    # ------------------------------------------------------------------
    path(
        "products/ratings/create/",
        views.ProductRatingCreateView.as_view(),
        name="product-rating-create"
    ),
    path(
        "products/<uuid:product_uuid>/ratings/",
        views.ProductRatingListView.as_view(),
        name="product-rating-list"
    ),

    # ------------------------------------------------------------------
    # 5. ADMIN / MANAGEMENT PRODUCTS
    # ------------------------------------------------------------------
    path(
        "products/management/",
        views.ProductListCreateAdminView.as_view(),
        name="product-management-list-create"
    ),
    path(
        "products/management/<uuid:uuid>/",
        views.ProductDetailAdminView.as_view(),
        name="product-management-detail"
    ),

    # ------------------------------------------------------------------
    # 6. SHOP LOCATIONS
    # ------------------------------------------------------------------
    path(
        "shop-location/",
        views.ShopLocationListCreateView.as_view(),
        name="shop-location-list"
    ),
    path(
        "shop-location/<int:pk>/",
        views.ShopLocationDetailView.as_view(),
        name="shop-location-detail"
    ),
]