from django.urls import re_path

from .consumers import BulkImportConsumer


websocket_urlpatterns = [

    re_path(
        r"ws/bulk-import/(?P<import_id>\d+)/$",
        BulkImportConsumer.as_asgi()
    ),
]