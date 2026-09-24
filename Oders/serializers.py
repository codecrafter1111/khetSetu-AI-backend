from rest_framework import serializers

class CheckoutSerializer(serializers.Serializer):
    address_id = serializers.IntegerField()
    payment_method = serializers.ChoiceField(
        choices=["COD", "UPI", "CARD"]
    )