from rest_framework import serializers
from .models import (
    DeliveryPartner,
    PartnerDocuments,
    PartnerLocation,
    DeliveryAssignment,
    RiderEarning
)


# 1. Partner Documents Serializer
class PartnerDocumentsSerializer(serializers.ModelSerializer):
    driving_license_url = serializers.SerializerMethodField()
    vehicle_rc_url = serializers.SerializerMethodField()
    aadhar_docs_url = serializers.SerializerMethodField()

    class Meta:
        model = PartnerDocuments
        fields = [
            'id',
            'partner',
            'Driving_licens',
            'driving_license_url',
            'Vehicle_Rc',
            'vehicle_rc_url',
            'Aadhar_docs',
            'aadhar_docs_url',
            'verified'
        ]
        read_only_fields = ['verified']
        extra_kwargs = {
            'Driving_licens': {'write_only': True},
            'Vehicle_Rc': {'write_only': True},
            'Aadhar_docs': {'write_only': True},
        }

    def get_driving_license_url(self, obj):
        return obj.Driving_licens.url if obj.Driving_licens else None

    def get_vehicle_rc_url(self, obj):
        return obj.Vehicle_Rc.url if obj.Vehicle_Rc else None

    def get_aadhar_docs_url(self, obj):
        return obj.Aadhar_docs.url if obj.Aadhar_docs else None


# 2. Partner Live Location Serializer
class PartnerLocationSerializer(serializers.ModelSerializer):
    rider_name = serializers.CharField(source='rider.fullName', read_only=True)

    class Meta:
        model = PartnerLocation
        fields = ['id', 'rider', 'rider_name', 'latitude', 'longitude', 'updated_at']


# 3. Delivery Partner Main Serializer
class DeliveryPartnerSerializer(serializers.ModelSerializer):
    profile_image_url = serializers.SerializerMethodField()
    documents = PartnerDocumentsSerializer(source='partner_document', read_only=True)
    location = PartnerLocationSerializer(source='delivery_partner', read_only=True)

    class Meta:
        model = DeliveryPartner
        fields = [
            'id',
            'user',
            'Partner_id',
            'profile_image',
            'profile_image_url',
            'fullName',
            'mobile',
            'Vehicle_type',
            'Vehicle_number',
            'is_online',
            'is_available',
            'is_verified',
            'rating',
            'total_deliveries',
            'documents',
            'location',
            'created_at'
        ]
        read_only_fields = ['is_verified', 'rating', 'total_deliveries', 'created_at']
        extra_kwargs = {
            'profile_image': {'write_only': True}
        }

    def get_profile_image_url(self, obj):
        return obj.profile_image.url if obj.profile_image else None


# 4. Delivery Assignment Serializer
class DeliveryAssignmentSerializer(serializers.ModelSerializer):
    rider_details = DeliveryPartnerSerializer(source='rider', read_only=True)
    order_id_code = serializers.CharField(source='order.order_id', read_only=True)

    class Meta:
        model = DeliveryAssignment
        fields = [
            'id',
            'order',
            'order_id_code',
            'rider',
            'rider_details',
            'status',
            'assigned_at',
            'delivered_at'
        ]
        read_only_fields = ['assigned_at']


# 5. Rider Earnings Serializer
class RiderEarningSerializer(serializers.ModelSerializer):
    rider_name = serializers.CharField(source='rider.fullName', read_only=True)
    order_id_code = serializers.CharField(source='order.order_id', read_only=True)
    total_earning = serializers.SerializerMethodField()

    class Meta:
        model = RiderEarning
        fields = [
            'id',
            'rider',
            'rider_name',
            'order',
            'order_id_code',
            'delivery_fee',
            'tip',
            'total_earning',
            'created_at'
        ]
        read_only_fields = ['created_at']

    def get_total_earning(self, obj):
        return float(obj.delivery_fee or 0) + float(obj.tip or 0)

from rest_framework import serializers
from Oders.models import Orders

class RiderActiveOrderSerializer(serializers.ModelSerializer):

    class Meta:
        model = Orders
        fields = [
            "order_id",
            "status",
            "address",
            "total_amount"
        ]


class CustomerTrackingSerializer(serializers.ModelSerializer):

    rider_name = serializers.CharField(
        source="delivery_partner.name",
        read_only=True
    )

    latitude = serializers.DecimalField(
        source="live_location.latitude",
        max_digits=10,
        decimal_places=7,
        read_only=True
    )

    longitude = serializers.DecimalField(
        source="live_location.longitude",
        max_digits=10,
        decimal_places=7,
        read_only=True
    )

    class Meta:
        model = Orders
        fields = [
            "order_id",
            "status",
            "rider_name",
            "total_amount",
            "latitude",
            "longitude"
        ]                