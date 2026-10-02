from rest_framework import serializers
from .models import Station, Platform, Facility


class FacilitySerializer(serializers.ModelSerializer):
    facility_type_display = serializers.CharField(source='get_facility_type_display', read_only=True)

    class Meta:
        model = Facility
        fields = [
            'id', 'station', 'platform', 'facility_type', 'facility_type_display',
            'name', 'location_description', 'latitude', 'longitude', 'is_operational',
            'contact_number', 'icon'
        ]


class PlatformSerializer(serializers.ModelSerializer):
    facilities = FacilitySerializer(many=True, read_only=True)

    class Meta:
        model = Platform
        fields = [
            'id', 'station', 'number', 'description', 'has_lift', 'has_escalator',
            'has_wheelchair_ramp', 'latitude', 'longitude', 'facilities'
        ]


class StationSerializer(serializers.ModelSerializer):
    platforms = PlatformSerializer(many=True, read_only=True)
    facilities = FacilitySerializer(many=True, read_only=True)

    class Meta:
        model = Station
        fields = [
            'id', 'name', 'code', 'city', 'state', 'number_of_platforms',
            'latitude', 'longitude', 'is_active', 'created_at', 'platforms', 'facilities'
        ]
