from rest_framework import serializers
from .models import LostFoundReport


class LostFoundReportSerializer(serializers.ModelSerializer):
    report_type_display = serializers.CharField(source='get_report_type_display', read_only=True)
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    station_name = serializers.CharField(source='station.name', read_only=True)
    station_code = serializers.CharField(source='station.code', read_only=True)

    class Meta:
        model = LostFoundReport
        fields = [
            'id', 'report_id', 'user', 'report_type', 'report_type_display',
            'item_name', 'category', 'category_display', 'description',
            'image', 'image_url', 'station', 'station_name', 'station_code',
            'platform', 'coach_number', 'incident_date', 'contact_name',
            'contact_phone', 'contact_email', 'status', 'status_display',
            'storage_location', 'admin_notes', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'report_id', 'created_at', 'updated_at']
