from rest_framework import serializers
from .models import Complaint


class ComplaintSerializer(serializers.ModelSerializer):
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    station_name = serializers.CharField(source='station.name', read_only=True)
    station_code = serializers.CharField(source='station.code', read_only=True)

    class Meta:
        model = Complaint
        fields = [
            'id', 'ticket_id', 'user', 'category', 'category_display',
            'station', 'station_name', 'station_code', 'platform', 'description',
            'image', 'image_url', 'contact_name', 'contact_phone', 'contact_email',
            'priority', 'priority_display', 'status', 'status_display',
            'assigned_officer', 'resolution_notes', 'created_at', 'updated_at', 'resolved_at'
        ]
        read_only_fields = ['id', 'ticket_id', 'created_at', 'updated_at']
