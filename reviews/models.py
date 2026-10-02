from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Review(models.Model):
    booking = models.OneToOneField('bookings.Booking', on_delete=models.CASCADE, related_name='review')
    passenger = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='given_reviews')
    coolie = models.ForeignKey('accounts.CoolieProfile', on_delete=models.CASCADE, related_name='reviews')
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        default=5,
        help_text="Overall Rating (1 to 5 Stars)"
    )
    punctuality_rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        default=5
    )
    behavior_rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        default=5
    )
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.rating}★ Review for {self.coolie.user.get_full_name()} by {self.passenger.username}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Automatically update coolie's average rating
        self.coolie.recalculate_rating()


class StationReview(models.Model):
    station = models.ForeignKey('stations.Station', on_delete=models.CASCADE, related_name='reviews')
    passenger = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='station_reviews')
    rating = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)], default=5)
    cleanliness_rating = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)], default=5)
    amenities_rating = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)], default=5)
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.rating}★ Review for {self.station.name}"
