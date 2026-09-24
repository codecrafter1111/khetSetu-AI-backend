from urllib.parse import parse_qs

from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser

from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.exceptions import (
    InvalidToken,
    TokenError,
)


User = get_user_model()


@database_sync_to_async
def get_user(user_id):
    try:
        return User.objects.get(id=user_id)
    except User.DoesNotExist:
        return AnonymousUser()


class JWTAuthMiddleware(BaseMiddleware):

    async def __call__(self, scope, receive, send):

        # Default user
        scope["user"] = AnonymousUser()

        # WebSocket query string
        query_string = scope.get(
            "query_string",
            b""
        ).decode()

        query_params = parse_qs(query_string)

        # ?token=xxxxx
        token = query_params.get(
            "token",
            [None]
        )[0]

        if token:

            try:
                # Validate JWT
                access_token = AccessToken(token)

                # Get user ID from JWT
                user_id = access_token.get("user_id")

                if user_id:
                    scope["user"] = await get_user(user_id)

            except (
                InvalidToken,
                TokenError,
                KeyError,
                TypeError,
                ValueError,
            ):
                scope["user"] = AnonymousUser()

        return await super().__call__(
            scope,
            receive,
            send
        )