from rest_framework import serializers
from .models import Review, StationReview


class ReviewSerializer(serializers.ModelSerializer):
    passenger_name = serializers.CharField(source='passenger.get_full_name', read_only=True)
    coolie_name = serializers.CharField(source='coolie.user.get_full_name', read_only=True)
    coolie_badge = serializers.CharField(source='coolie.badge_number', read_only=True)

    class Meta:
        model = Review
        fields = [
            'id', 'booking', 'passenger', 'passenger_name', 'coolie', 'coolie_name',
            'coolie_badge', 'rating', 'punctuality_rating', 'behavior_rating', 'comment', 'created_at'
        ]
        read_only_fields = ['id', 'passenger', 'created_at']


class StationReviewSerializer(serializers.ModelSerializer):
    passenger_name = serializers.CharField(source='passenger.get_full_name', read_only=True)
    station_name = serializers.CharField(source='station.name', read_only=True)

    class Meta:
        model = StationReview
        fields = [
            'id', 'station', 'station_name', 'passenger', 'passenger_name',
            'rating', 'cleanliness_rating', 'amenities_rating', 'comment', 'created_at'
        ]
        read_only_fields = ['id', 'passenger', 'created_at']
