import json

from channels.generic.websocket import AsyncWebsocketConsumer


class BulkImportConsumer(AsyncWebsocketConsumer):

    async def connect(self):

        # JWT Middleware se user
        self.user = self.scope["user"]

        # Authentication check
        if not self.user.is_authenticated:
            await self.close(code=4001)
            return

        # Import ID
        self.import_id = self.scope[
            "url_route"
        ]["kwargs"]["import_id"]

        # Group name
        self.group_name = (
            f"bulk_import_{self.import_id}"
        )

        # Join group
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name,
        )

        # Accept connection
        await self.accept()

        print(
            f"WebSocket connected: "
            f"user={self.user.id}, "
            f"import={self.import_id}"
        )

    async def disconnect(self, close_code):

        # Remove from group
        if hasattr(self, "group_name"):

            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name,
            )

        print(
            f"WebSocket disconnected: "
            f"user={self.user.id if hasattr(self, 'user') else None}, "
            f"import={getattr(self, 'import_id', None)}, "
            f"code={close_code}"
        )

    async def bulk_import_progress(self, event):

        await self.send(
            text_data=json.dumps(
                {
                    "import_id": event["import_id"],
                    "status": event["status"],
                    "processed": event["processed"],
                    "total": event["total"],
                    "created": event["created"],
                    "skipped": event["skipped"],
                    "failed": event["failed"],
                    "percentage": event["percentage"],
                }
            )
        )