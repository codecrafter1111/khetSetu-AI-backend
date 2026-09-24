from django.urls import path
from .views import RiderFeedbackCreateView,RiderDashboardView

urlpatterns = [
    path(
        "rider-feedback/",
        RiderFeedbackCreateView.as_view(),
        name="rider-feedback"
    ),
    path(
        "rider/dashboard/",
        RiderDashboardView.as_view(),
        name="rider-dashboard"
    ),
]