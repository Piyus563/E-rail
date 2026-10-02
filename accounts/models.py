from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    ROLE_CHOICES = [
        ('PASSENGER', 'Passenger'),
        ('COOLIE', 'Coolie (Sahayak)'),
        ('ADMIN', 'Station Administrator'),
    ]

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='PASSENGER')
    phone = models.CharField(max_length=20, unique=True, null=True, blank=True)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    is_phone_verified = models.BooleanField(default=False)

    def is_passenger(self):
        return self.role == 'PASSENGER'

    def is_coolie(self):
        return self.role == 'COOLIE'

    def is_station_admin(self):
        return self.role == 'ADMIN' or self.is_superuser


class PassengerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='passenger_profile')
    emergency_contact = models.CharField(max_length=20, blank=True)
    preferred_language = models.CharField(max_length=50, default='English')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Passenger: {self.user.get_full_name() or self.user.username}"


class CoolieProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='coolie_profile')
    badge_number = models.CharField(max_length=50, unique=True, help_text="Railway Licensed Badge Number (e.g. NJP-C-104)")
    station = models.ForeignKey('stations.Station', on_delete=models.SET_NULL, null=True, blank=True, related_name='coolies')
    experience_years = models.PositiveIntegerField(default=3)
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=5.00)
    total_ratings_count = models.PositiveIntegerField(default=1)
    is_verified = models.BooleanField(default=True)
    is_online = models.BooleanField(default=True)
    current_platform = models.ForeignKey('stations.Platform', on_delete=models.SET_NULL, null=True, blank=True)
    daily_earnings = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_bookings_count = models.PositiveIntegerField(default=0)
    id_proof_number = models.CharField(max_length=50, blank=True)
    photo_url = models.CharField(max_length=500, blank=True, help_text="Fallback photo URL or avatar image path")

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} (Badge: {self.badge_number})"

    class Meta:
        ordering = ['-rating', '-experience_years']

    def recalculate_rating(self):
        from reviews.models import Review
        reviews = Review.objects.filter(coolie=self)
        if reviews.exists():
            avg_rating = reviews.aggregate(models.Avg('rating'))['rating__avg']
            self.rating = round(avg_rating, 2)
            self.total_ratings_count = reviews.count()
            self.save(update_fields=['rating', 'total_ratings_count'])


class AuditLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=255)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    details = models.TextField(blank=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.timestamp.strftime('%Y-%m-%d %H:%M')} - {self.action}"
