from django.urls import path
from .views import CartView,CheckoutOrderView
urlpatterns=[
  path('cart/', CartView.as_view(), name='cart-management'),
  path("checkout/", CheckoutOrderView.as_view(), name="checkout"),
]

