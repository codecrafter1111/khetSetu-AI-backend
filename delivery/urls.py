from django.urls import path

from .views import (
    DeliveryPartnerProfileView,
    DeliveryPartnerRegistrationView,
    ToggleOnlineStatusView,
    PartnerDocumentUploadView,
)


app_name = "delivery_partner"


urlpatterns = [
      path("profile/",DeliveryPartnerProfileView.as_view(),name="profile",),
      path("register/",DeliveryPartnerRegistrationView.as_view(),name="register",),
      path("status/",ToggleOnlineStatusView.as_view(),name="status",),
      path("documents/",PartnerDocumentUploadView.as_view(),name="documents",),
]