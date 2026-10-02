from rest_framework import serializers
from .models import AssistanceRequest


class AssistanceRequestSerializer(serializers.ModelSerializer):
    assistance_type_display = serializers.CharField(source='get_assistance_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    station_name = serializers.CharField(source='station.name', read_only=True)
    station_code = serializers.CharField(source='station.code', read_only=True)
    platform_number = serializers.IntegerField(source='platform.number', read_only=True)

    class Meta:
        model = AssistanceRequest
        fields = [
            'id', 'request_id', 'passenger', 'passenger_name', 'passenger_phone',
            'station', 'station_name', 'station_code', 'platform', 'platform_number',
            'coach_number', 'train_number', 'assistance_type', 'assistance_type_display',
            'description', 'status', 'status_display', 'assigned_staff_name',
            'assigned_staff_phone', 'staff_notes', 'created_at', 'updated_at', 'resolved_at'
        ]
        read_only_fields = ['id', 'request_id', 'created_at', 'updated_at']
