from rest_framework import serializers
from .models import AddToCart, Products
from Products.productserializer import ProductSerializer

# Read Serializer (Cart list render karne ke liye)
class CartItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    total_price = serializers.ReadOnlyField()  # Model @property

    class Meta:
        model = AddToCart
        fields = ['id', 'product', 'quantity', 'total_price', 'created_at']


# Write Serializer (Cart me product add karne ke liye)
# CHANGED: product_id ab UUIDField hai, kyunki ProductSerializer response
# me sirf `uuid` expose hota hai — internal integer `id` nahi. Frontend
# ke paas asal me sirf uuid hi available hota hai, isliye backend ko
# wahi accept karna chahiye.
class AddToCartSerializer(serializers.Serializer):
    product_id = serializers.UUIDField()
    quantity = serializers.IntegerField(default=1, min_value=1)