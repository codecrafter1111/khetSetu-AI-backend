from rest_framework import serializers
from .models import BuyerShipping

from rest_framework import serializers
from .models import BuyerShipping

class BuyerShippingSerializer(serializers.ModelSerializer):
    # Optional fields standardisation & Decimal handling
    landmark = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    opposite_of = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    
    latitude = serializers.DecimalField(
        max_digits=10, 
        decimal_places=8, 
        required=False, 
        allow_null=True
    )
    longitude = serializers.DecimalField(
        max_digits=11, 
        decimal_places=8, 
        required=False, 
        allow_null=True
    )

    class Meta:
        model = BuyerShipping
        fields = [
            'id',
            'full_name',
            'mobile_number',
            'address_line',
            'landmark',
            'opposite_of',
            'city',
            'state',
            'zip_code',
            'address_type',
            'latitude',
            'longitude',
            'is_default',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at']

    def create(self, validated_data):
        user = self.context['request'].user
        
        # Agar current address default set ho raha hai, toh baki purane addresses ko non-default kar do
        if validated_data.get('is_default', False):
            BuyerShipping.objects.filter(user=user, is_default=True).update(is_default=False)

        return BuyerShipping.objects.create(user=user, **validated_data)