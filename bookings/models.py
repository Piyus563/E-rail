import uuid
from django.db import models
from django.utils import timezone


def generate_booking_id():
    return f"RS-BKG-{uuid.uuid4().hex[:6].upper()}"


class Booking(models.Model):
    JOURNEY_TYPES = [
        ('ARRIVAL', 'Train Arrival (De-boarding)'),
        ('DEPARTURE', 'Train Departure (Boarding)'),
    ]

    LUGGAGE_TYPES = [
        ('TROLLEY', 'Trolley Bags / Suitcases'),
        ('HEAVY_BAGS', 'Duffel / Heavy Rucksacks'),
        ('BOXES', 'Carton Boxes / Packages'),
        ('COMBINED', 'Mixed / Multiple Luggage'),
    ]

    STATUS_CHOICES = [
        ('REQUESTED', 'Requested (Waiting for Coolie)'),
        ('ACCEPTED', 'Accepted by Coolie'),
        ('REJECTED', 'Rejected'),
        ('SERVICE_STARTED', 'Service Started (Coolie Reached)'),
        ('COMPLETED', 'Service Completed'),
        ('CANCELLED', 'Cancelled'),
    ]

    booking_id = models.CharField(max_length=30, unique=True, default=generate_booking_id)
    passenger = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='bookings')
    coolie = models.ForeignKey('accounts.CoolieProfile', on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_bookings')
    station = models.ForeignKey('stations.Station', on_delete=models.CASCADE, related_name='bookings')
    platform = models.ForeignKey('stations.Platform', on_delete=models.SET_NULL, null=True, blank=True, related_name='bookings')

    journey_type = models.CharField(max_length=20, choices=JOURNEY_TYPES, default='ARRIVAL')
    train_number = models.CharField(max_length=20, blank=True, help_text="e.g. 12042 New Jalpaiguri Shatabdi")
    train_name = models.CharField(max_length=100, blank=True)
    coach_number = models.CharField(max_length=20, blank=True, help_text="e.g. B2, C1, S4")
    seat_number = models.CharField(max_length=20, blank=True, help_text="e.g. 45, 52")

    luggage_type = models.CharField(max_length=30, choices=LUGGAGE_TYPES, default='TROLLEY')
    number_of_bags = models.PositiveIntegerField(default=2)
    approx_weight_kg = models.PositiveIntegerField(default=25)
    special_notes = models.TextField(blank=True, help_text="e.g. Elderly passenger travelling, need wheelchair along with coolie")

    meeting_point = models.CharField(max_length=200, blank=True, default="Platform 1 Main Entrance")
    scheduled_time = models.DateTimeField(default=timezone.now)

    base_fare = models.DecimalField(max_digits=8, decimal_places=2, default=120.00)
    extra_bag_fare = models.DecimalField(max_digits=8, decimal_places=2, default=60.00)
    total_fare = models.DecimalField(max_digits=8, decimal_places=2, default=180.00)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='REQUESTED')
    cancellation_reason = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    accepted_at = models.DateTimeField(null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.booking_id} - {self.passenger.username} -> {self.coolie or 'Unassigned'}"

    def calculate_fare(self):
        # Base fare covers up to 1 bag
        base = 100.00
        per_extra_bag = 50.00
        extra_bags = max(0, self.number_of_bags - 1)
        self.base_fare = base
        self.extra_bag_fare = extra_bags * per_extra_bag
        self.total_fare = self.base_fare + self.extra_bag_fare
        return self.total_fare
