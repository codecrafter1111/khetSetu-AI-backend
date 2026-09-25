from rest_framework import serializers
from .models import ShopLocation

class ShopLocationSerializer(serializers.ModelSerializer):
    owner = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = ShopLocation
        fields = [
            "id",
            "owner",
            "name",
            "address",
            "latitude",
            "longitude",
        ]
        read_only_fields = ["id", "owner"]