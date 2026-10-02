from rest_framework import serializers
from .models import User, PassengerProfile, CoolieProfile, AuditLog


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'role', 'phone', 'is_phone_verified']
        read_only_fields = ['id', 'role']


class PassengerProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = PassengerProfile
        fields = ['id', 'user', 'emergency_contact', 'preferred_language', 'created_at']


class CoolieProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    station_name = serializers.CharField(source='station.name', read_only=True)
    station_code = serializers.CharField(source='station.code', read_only=True)
    platform_number = serializers.IntegerField(source='current_platform.number', read_only=True)

    class Meta:
        model = CoolieProfile
        fields = [
            'id', 'user', 'badge_number', 'station', 'station_name', 'station_code',
            'experience_years', 'rating', 'total_ratings_count', 'is_verified', 'is_online',
            'current_platform', 'platform_number', 'daily_earnings', 'total_bookings_count',
            'photo_url'
        ]
        read_only_fields = ['id', 'rating', 'total_ratings_count', 'daily_earnings', 'total_bookings_count']
