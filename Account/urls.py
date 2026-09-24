from django.urls import path,include
from Account.views import RegisterView,LoginView,OtpView,ResendView,Logout,Profile
from .views import  *

from django.http import JsonResponse

def test_api(request):
    print("🔥 TEST API HIT")
    return JsonResponse({
        "message": "API working"
    })



urlpatterns = [
    path('Account/Registration/',RegisterView.as_view(),name='register'),
    path('login/',LoginView.as_view(),name='login'),
    path('resend-otp/',ResendView.as_view(),name='resend_otp'),
    path('verify-otp/',OtpView.as_view(),name='verify-otp'),
    path('Profile/',Profile.as_view(),name='Profile'),
    path('logout/',Logout.as_view(),name='logout'),
    
    path(
        "test/",
        test_api,
        name="test"
    ),

  
  # shipping address urls
     path(
        'shipping/create/',
        ShippingAddressCreate.as_view()
    ),
    path('shipping/list/',ShippingAddressList.as_view()),
    path('shipping/update/<int:id>/',ShippingAddressUpdate.as_view()),

    path('shipping/delete/<int:id>/',ShippingAddressDelete.as_view()),
    path('shipping/default/<int:id>/',SetDefaultAddress.as_view()),

    path('shipping/current-default/',DefaultAddress.as_view()),
   
]