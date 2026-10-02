from rest_framework import serializers
from .models import Booking
from accounts.serializers import UserSerializer, CoolieProfileSerializer
from stations.serializers import StationSerializer, PlatformSerializer


class BookingSerializer(serializers.ModelSerializer):
    passenger_details = UserSerializer(source='passenger', read_only=True)
    coolie_details = CoolieProfileSerializer(source='coolie', read_only=True)
    station_name = serializers.CharField(source='station.name', read_only=True)
    station_code = serializers.CharField(source='station.code', read_only=True)
    platform_number = serializers.IntegerField(source='platform.number', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    journey_type_display = serializers.CharField(source='get_journey_type_display', read_only=True)
    luggage_type_display = serializers.CharField(source='get_luggage_type_display', read_only=True)

    class Meta:
        model = Booking
        fields = [
            'id', 'booking_id', 'passenger', 'passenger_details', 'coolie', 'coolie_details',
            'station', 'station_name', 'station_code', 'platform', 'platform_number',
            'journey_type', 'journey_type_display', 'train_number', 'train_name',
            'coach_number', 'seat_number', 'luggage_type', 'luggage_type_display',
            'number_of_bags', 'approx_weight_kg', 'special_notes', 'meeting_point',
            'scheduled_time', 'base_fare', 'extra_bag_fare', 'total_fare', 'status',
            'status_display', 'cancellation_reason', 'created_at', 'updated_at',
            'accepted_at', 'started_at', 'completed_at'
        ]
        read_only_fields = ['id', 'booking_id', 'passenger', 'base_fare', 'extra_bag_fare', 'total_fare', 'created_at', 'updated_at']

    def create(self, validated_data):
        booking = Booking(**validated_data)
        booking.calculate_fare()
        booking.save()
        return booking
