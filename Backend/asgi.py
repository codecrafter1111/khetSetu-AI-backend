import os

from django.core.asgi import get_asgi_application

from channels.routing import (
    ProtocolTypeRouter,
    URLRouter,
)

from Realtime.middleware import JWTAuthMiddleware
from Products.routing import websocket_urlpatterns
from Realtime.routing import websocket_urlpatterns as realtime_websocket_urlpatterns


os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "Backend.settings"
)


django_asgi_app = get_asgi_application()


application = ProtocolTypeRouter({

    "http": django_asgi_app,

    "websocket": JWTAuthMiddleware(
        URLRouter(
            websocket_urlpatterns + realtime_websocket_urlpatterns
        )
    ),

})