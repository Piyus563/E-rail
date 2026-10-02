from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from rest_framework import viewsets, permissions
from rest_framework.exceptions import PermissionDenied

from .models import Review, StationReview
from .serializers import ReviewSerializer, StationReviewSerializer
from bookings.models import Booking


@login_required
def submit_review_view(request, booking_id):
    """
    Submit a review for a completed booking.
    """
    booking = get_object_or_404(Booking, booking_id=booking_id, passenger=request.user)

    if booking.status != 'COMPLETED':
        messages.error(request, "You can only review completed bookings.")
        return redirect('bookings:tracking', booking_id=booking.booking_id)

    if request.method == 'POST':
        rating = int(request.POST.get('rating', 5))
        punctuality_rating = int(request.POST.get('punctuality_rating', 5))
        behavior_rating = int(request.POST.get('behavior_rating', 5))
        comment = request.POST.get('comment', '').strip()

        Review.objects.update_or_create(
            booking=booking,
            defaults={
                'passenger': request.user,
                'coolie': booking.coolie,
                'rating': rating,
                'punctuality_rating': punctuality_rating,
                'behavior_rating': behavior_rating,
                'comment': comment,
            }
        )
        messages.success(request, "Your review has been saved! Thank you for helping the community.")
        return redirect('bookings:tracking', booking_id=booking.booking_id)

    return redirect('bookings:tracking', booking_id=booking.booking_id)


# --- REST API ViewSets ---

class ReviewViewSet(viewsets.ModelViewSet):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(passenger=self.request.user)

    def perform_update(self, serializer):
        review = self.get_object()
        if review.passenger != self.request.user and not self.request.user.is_staff:
            raise PermissionDenied("You can only edit your own reviews.")
        serializer.save()

    def perform_destroy(self, instance):
        if instance.passenger != self.request.user and not self.request.user.is_staff:
            raise PermissionDenied("You can only delete your own reviews.")
        instance.delete()


class StationReviewViewSet(viewsets.ModelViewSet):
    queryset = StationReview.objects.all()
    serializer_class = StationReviewSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(passenger=self.request.user)

    def perform_update(self, serializer):
        review = self.get_object()
        if review.passenger != self.request.user and not self.request.user.is_staff:
            raise PermissionDenied("You can only edit your own reviews.")
        serializer.save()

    def perform_destroy(self, instance):
        if instance.passenger != self.request.user and not self.request.user.is_staff:
            raise PermissionDenied("You can only delete your own reviews.")
        instance.delete()
