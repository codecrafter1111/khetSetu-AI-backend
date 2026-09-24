from django.urls import re_path
from .consumer import OrderTrackingConsumer

websocket_urlpatterns = [
    re_path(
        r"ws/order/(?P<order_id>[\w-]+)/$",
        OrderTrackingConsumer.as_asgi(),
    ),
]