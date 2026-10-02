from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db import transaction as db_transaction
from django.db.models import F
from decimal import Decimal
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action

from .models import Booking
from .serializers import BookingSerializer
from .whatsapp import (
    notify_booking_created, notify_booking_accepted,
    notify_booking_started, notify_booking_completed,
    notify_booking_cancelled, notify_booking_rejected
)
from accounts.models import CoolieProfile, User
from stations.models import Station, Platform
from reviews.models import Review
from notifications.models import Notification


# --- HTML Views ---

@login_required
def book_coolie_view(request):
    """
    Primary MVP Booking Wizard: Station -> Platform -> Luggage -> Coolie Selection -> Live Fare -> Confirmation.
    """
    stations = Station.objects.filter(is_active=True)
    selected_station_code = request.GET.get('station', 'NJP')
    station = Station.objects.filter(code__iexact=selected_station_code).first() or stations.first()
    platforms = station.platforms.all() if station else []

    # Get available online verified coolies for this station
    available_coolies = CoolieProfile.objects.filter(
        station=station,
        is_verified=True,
        is_online=True
    )

    if request.method == 'POST':
        station_id = request.POST.get('station_id')
        platform_id = request.POST.get('platform_id')
        coolie_id = request.POST.get('coolie_id')
        journey_type = request.POST.get('journey_type', 'ARRIVAL')
        if journey_type not in dict(Booking.JOURNEY_TYPES):
            journey_type = 'ARRIVAL'
        train_number = request.POST.get('train_number', '').strip()
        train_name = request.POST.get('train_name', '').strip()
        coach_number = request.POST.get('coach_number', '').strip()
        seat_number = request.POST.get('seat_number', '').strip()
        luggage_type = request.POST.get('luggage_type', 'TROLLEY')
        if luggage_type not in dict(Booking.LUGGAGE_TYPES):
            luggage_type = 'TROLLEY'
        try:
            number_of_bags = max(1, min(20, int(request.POST.get('number_of_bags', 1))))
        except (ValueError, TypeError):
            number_of_bags = 1
        try:
            approx_weight_kg = max(1, min(500, int(request.POST.get('approx_weight_kg', 20))))
        except (ValueError, TypeError):
            approx_weight_kg = 20
        meeting_point = request.POST.get('meeting_point', '').strip()
        special_notes = request.POST.get('special_notes', '').strip()

        stn_obj = get_object_or_404(Station, id=station_id)
        plat_obj = Platform.objects.filter(id=platform_id).first() if platform_id else None
        coolie_obj = CoolieProfile.objects.filter(id=coolie_id).first() if coolie_id else available_coolies.first()

        with db_transaction.atomic():
            booking = Booking(
                passenger=request.user,
                coolie=coolie_obj,
                station=stn_obj,
                platform=plat_obj,
                journey_type=journey_type,
                train_number=train_number,
                train_name=train_name,
                coach_number=coach_number,
                seat_number=seat_number,
                luggage_type=luggage_type,
                number_of_bags=number_of_bags,
                approx_weight_kg=approx_weight_kg,
                meeting_point=meeting_point or f"Platform {plat_obj.number if plat_obj else '1'} Main Gate",
                special_notes=special_notes,
                status='REQUESTED'
            )
            booking.calculate_fare()
            booking.save()

            # Send notification to coolie if assigned
            if coolie_obj:
                Notification.objects.create(
                    recipient=coolie_obj.user,
                    title="New Booking Request Received 🧳",
                    message=f"Passenger {request.user.get_full_name() or request.user.username} requested luggage assistance at Platform {plat_obj.number if plat_obj else '1'}. Fare: ₹{booking.total_fare}",
                    notification_type='BOOKING',
                    link_url="/coolies/dashboard/"
                )

        # WhatsApp notification to passenger
        notify_booking_created(booking)

        messages.success(request, f"Booking request #{booking.booking_id} created successfully! Waiting for coolie confirmation.")
        return redirect('bookings:tracking', booking_id=booking.booking_id)

    context = {
        'stations': stations,
        'current_station': station,
        'platforms': platforms,
        'available_coolies': available_coolies,
    }
    return render(request, 'bookings/book_coolie.html', context)


@login_required
def booking_tracking_view(request, booking_id):
    """
    Visual Timeline Tracking Page for passenger bookings with Coolie profile card & Review form.
    """
    booking = get_object_or_404(Booking, booking_id=booking_id)

    # Check permission (passenger, assigned coolie, or admin)
    if not (booking.passenger == request.user or (hasattr(request.user, 'coolie_profile') and booking.coolie == request.user.coolie_profile) or request.user.role == 'ADMIN' or request.user.is_superuser):
        messages.error(request, "Unauthorized access to this booking.")
        return redirect('accounts:passenger_dashboard')

    existing_review = getattr(booking, 'review', None)

    # Handle review submission
    if request.method == 'POST' and 'submit_review' in request.POST and booking.status == 'COMPLETED':
        if existing_review:
            messages.info(request, "You have already submitted a review for this booking.")
        else:
            rating = int(request.POST.get('rating', 5))
            punctuality = int(request.POST.get('punctuality_rating', 5))
            behavior = int(request.POST.get('behavior_rating', 5))
            comment = request.POST.get('comment', '').strip()

            Review.objects.create(
                booking=booking,
                passenger=request.user,
                coolie=booking.coolie,
                rating=rating,
                punctuality_rating=punctuality,
                behavior_rating=behavior,
                comment=comment
            )
            messages.success(request, "Thank you! Your rating and review have been submitted.")
            return redirect('bookings:tracking', booking_id=booking.booking_id)

    # Handle cancellation
    if request.method == 'POST' and 'cancel_booking' in request.POST:
        if booking.status in ['REQUESTED', 'ACCEPTED']:
            reason = request.POST.get('cancellation_reason', 'Cancelled by passenger')
            booking.status = 'CANCELLED'
            booking.cancellation_reason = reason
            booking.save()

            if booking.coolie:
                Notification.objects.create(
                    recipient=booking.coolie.user,
                    title="Booking Cancelled",
                    message=f"Booking {booking.booking_id} was cancelled by passenger.",
                    notification_type='BOOKING',
                    link_url="/coolies/dashboard/"
                )
            notify_booking_cancelled(booking)
            messages.info(request, "Your booking has been cancelled.")
            return redirect('bookings:tracking', booking_id=booking.booking_id)

    context = {
        'booking': booking,
        'existing_review': existing_review,
    }
    return render(request, 'bookings/booking_tracking.html', context)


@login_required
def booking_history_view(request):
    """
    List of past and active bookings for the logged-in passenger.
    """
    bookings = Booking.objects.filter(passenger=request.user).order_by('-created_at')
    return render(request, 'bookings/booking_history.html', {'bookings': bookings})


# --- REST API ViewSets ---

class BookingViewSet(viewsets.ModelViewSet):
    serializer_class = BookingSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == 'ADMIN' or user.is_superuser:
            return Booking.objects.all()
        elif user.role == 'COOLIE' and hasattr(user, 'coolie_profile'):
            return Booking.objects.filter(coolie=user.coolie_profile)
        return Booking.objects.filter(passenger=user)

    def perform_create(self, serializer):
        serializer.save(passenger=self.request.user)

    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        booking = self.get_object()
        new_status = request.data.get('status')
        if new_status not in dict(Booking.STATUS_CHOICES):
            return Response({'error': 'Invalid status'}, status=status.HTTP_400_BAD_REQUEST)

        with db_transaction.atomic():
            booking.status = new_status
            if new_status == 'ACCEPTED':
                booking.accepted_at = timezone.now()
            elif new_status == 'SERVICE_STARTED':
                booking.started_at = timezone.now()
            elif new_status == 'COMPLETED':
                booking.completed_at = timezone.now()
                booking.save()
                # Use F() to avoid race condition on concurrent completions
                if booking.coolie_id:
                    from accounts.models import CoolieProfile
                    CoolieProfile.objects.filter(pk=booking.coolie_id).update(
                        total_bookings_count=F('total_bookings_count') + 1,
                        daily_earnings=F('daily_earnings') + booking.total_fare,
                    )
                return Response({'status': 'updated', 'booking_status': booking.status})
            booking.save()

        return Response({'status': 'updated', 'booking_status': booking.status})
