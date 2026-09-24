import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer

from Oders.models import Orders
from delivery.models import (
    PartnerLocation,
    DeliveryAssignment
)


class OrderTrackingConsumer(AsyncWebsocketConsumer):

    async def connect(self):

        self.user = self.scope["user"]

        if self.user.is_anonymous:
            await self.close(code=4001)
            return

        self.order_id = self.scope["url_route"]["kwargs"]["order_id"]
        self.room_name = f"order_{self.order_id}"

        allowed = await self.is_authorized()

        if not allowed:
            await self.close(code=4003)
            return

        await self.channel_layer.group_add(
            self.room_name,
            self.channel_name
        )

        await self.accept()

        location = await self.get_last_location()

        if location:
            await self.send(text_data=json.dumps({
                "type": "initial_location",
                **location
            }))

    async def disconnect(self, close_code):

        await self.channel_layer.group_discard(
            self.room_name,
            self.channel_name
        )

    async def receive(self, text_data):

        # Customer can't send GPS
        if not await self.is_rider():
            return

        try:

            data = json.loads(text_data)

            latitude = float(data["latitude"])
            longitude = float(data["longitude"])
            status = data.get("status", "on_the_way")

        except Exception:
            return

        await self.save_location(
            latitude,
            longitude,
            status
        )

        await self.channel_layer.group_send(
            self.room_name,
            {
                "type": "location_update",
                "latitude": latitude,
                "longitude": longitude,
                "status": status
            }
        )

    async def location_update(self, event):

        await self.send(text_data=json.dumps({
            "type": "live_location",
            "latitude": event["latitude"],
            "longitude": event["longitude"],
            "status": event["status"]
        }))

    # ==================================================
    # DATABASE
    # ==================================================

    @database_sync_to_async
    def is_authorized(self):

        try:

            order = Orders.objects.select_related(
                "user",
                "delivery_partner__user"
            ).get(order_id=self.order_id)

            if order.user == self.user:
                return True

            if (
                order.delivery_partner and
                order.delivery_partner.user == self.user
            ):
                return True

            return False

        except Orders.DoesNotExist:
            return False

    @database_sync_to_async
    def is_rider(self):

        try:

            order = Orders.objects.select_related(
                "delivery_partner__user"
            ).get(order_id=self.order_id)

            return (
                order.delivery_partner and
                order.delivery_partner.user == self.user
            )

        except Orders.DoesNotExist:
            return False

    @database_sync_to_async
    def save_location(self, lat, lng, status):

        order = Orders.objects.select_related(
            "delivery_partner"
        ).get(order_id=self.order_id)

        PartnerLocation.objects.update_or_create(
            rider=order.delivery_partner,
            defaults={
                "latitude": lat,
                "longitude": lng
            }
        )

        DeliveryAssignment.objects.filter(
            order=order
        ).update(status=status)

        order.status = status
        order.save(update_fields=["status"])

    @database_sync_to_async
    def get_last_location(self):

        try:

            order = Orders.objects.select_related(
                "delivery_partner"
            ).get(order_id=self.order_id)

            location = PartnerLocation.objects.get(
                rider=order.delivery_partner
            )

            assignment = DeliveryAssignment.objects.get(
                order=order
            )

            return {
                "latitude": float(location.latitude),
                "longitude": float(location.longitude),
                "status": assignment.status
            }

        except (
            Orders.DoesNotExist,
            PartnerLocation.DoesNotExist,
            DeliveryAssignment.DoesNotExist,
        ):
            return None