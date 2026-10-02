from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from decimal import Decimal

from accounts.models import CoolieProfile, User
from stations.models import Station, Platform
from bookings.models import Booking
from bookings.whatsapp import (
    notify_booking_accepted, notify_booking_started,
    notify_booking_completed, notify_booking_rejected
)
from reviews.models import Review
from notifications.models import Notification


def coolie_list_view(request):
    """
    Public listing of verified railway coolies with station filtering.
    """
    station_code = request.GET.get('station', '')
    coolies = CoolieProfile.objects.filter(is_verified=True)

    if station_code:
        coolies = coolies.filter(station__code__iexact=station_code)

    stations = Station.objects.filter(is_active=True)

    return render(request, 'coolie/coolie_list.html', {
        'coolies': coolies,
        'stations': stations,
        'selected_station': station_code
    })


def coolie_detail_view(request, pk):
    """
    Public profile of a coolie with ratings and passenger testimonials.
    """
    coolie = get_object_or_404(CoolieProfile, pk=pk)
    reviews = Review.objects.filter(coolie=coolie)[:10]

    return render(request, 'coolie/coolie_detail.html', {
        'coolie': coolie,
        'reviews': reviews
    })


@login_required
def coolie_dashboard_view(request):
    """
    Dedicated Coolie / Sahayak Dashboard with instant status toggle and booking request management.
    """
    if not (request.user.role == 'COOLIE' or hasattr(request.user, 'coolie_profile')):
        messages.error(request, "Access restricted to registered coolie partners.")
        return redirect('accounts:passenger_dashboard')

    coolie = request.user.coolie_profile

    # Handle Online/Offline toggle
    if request.method == 'POST' and 'toggle_status' in request.POST:
        coolie.is_online = not coolie.is_online
        coolie.save(update_fields=['is_online'])
        status_str = "Online (Ready for Bookings)" if coolie.is_online else "Offline"
        messages.success(request, f"Your availability status changed to: {status_str}")
        return redirect('coolies:dashboard')

    # Booking requests and tasks
    pending_requests = Booking.objects.filter(
        coolie=coolie,
        status='REQUESTED'
    ).order_by('-created_at')

    active_tasks = Booking.objects.filter(
        coolie=coolie,
        status__in=['ACCEPTED', 'SERVICE_STARTED']
    ).order_by('-created_at')

    completed_tasks = Booking.objects.filter(
        coolie=coolie,
        status='COMPLETED'
    ).order_by('-completed_at')[:10]

    # Calculate statistics
    today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    today_completed = Booking.objects.filter(coolie=coolie, status='COMPLETED', completed_at__gte=today_start)
    today_earnings = sum(b.total_fare for b in today_completed) or Decimal('0.00')

    reviews = Review.objects.filter(coolie=coolie)[:5]

    context = {
        'coolie': coolie,
        'pending_requests': pending_requests,
        'active_tasks': active_tasks,
        'completed_tasks': completed_tasks,
        'today_earnings': today_earnings,
        'today_count': today_completed.count(),
        'reviews': reviews,
    }
    return render(request, 'coolie/dashboard.html', context)


@login_required
def update_booking_status(request, booking_id, action):
    """
    Coolie action handler to Accept, Reject, Start Service, or Complete Service.
    Requires POST to prevent CSRF-via-GET attacks on state-changing operations.
    """
    if request.method != 'POST':
        messages.error(request, "Invalid request method.")
        return redirect('coolies:dashboard')

    if not (request.user.role == 'COOLIE' and hasattr(request.user, 'coolie_profile')):
        messages.error(request, "Unauthorized action.")
        return redirect('landing')

    coolie = request.user.coolie_profile
    booking = get_object_or_404(Booking, booking_id=booking_id, coolie=coolie)
    now = timezone.now()

    if action == 'accept' and booking.status == 'REQUESTED':
        booking.status = 'ACCEPTED'
        booking.accepted_at = now
        booking.save()
        Notification.objects.create(
            recipient=booking.passenger,
            title="Coolie Accepted Your Booking! 🎉",
            message=f"Sahayak {coolie.user.get_full_name()} accepted your booking ({booking.booking_id}) at Platform {booking.platform.number if booking.platform else '1'}.",
            notification_type='BOOKING',
            link_url=f"/bookings/track/{booking.booking_id}/"
        )
        notify_booking_accepted(booking)
        messages.success(request, f"Booking {booking.booking_id} accepted! Please reach the meeting point.")

    elif action == 'reject' and booking.status == 'REQUESTED':
        booking.status = 'REJECTED'
        booking.save()
        Notification.objects.create(
            recipient=booking.passenger,
            title="Booking Update",
            message=f"Coolie was unable to accept booking {booking.booking_id}. Please re-assign another available coolie.",
            notification_type='BOOKING',
            link_url="/bookings/book/"
        )
        notify_booking_rejected(booking)
        messages.warning(request, f"Booking {booking.booking_id} declined.")

    elif action == 'start' and booking.status == 'ACCEPTED':
        booking.status = 'SERVICE_STARTED'
        booking.started_at = now
        booking.save()
        Notification.objects.create(
            recipient=booking.passenger,
            title="Service Started 🧳",
            message=f"Sahayak {coolie.user.get_full_name()} has met you and started handling your luggage.",
            notification_type='BOOKING',
            link_url=f"/bookings/track/{booking.booking_id}/"
        )
        notify_booking_started(booking)
        messages.info(request, f"Service started for booking {booking.booking_id}.")

    elif action == 'complete' and booking.status == 'SERVICE_STARTED':
        booking.status = 'COMPLETED'
        booking.completed_at = now
        booking.save()
        coolie.total_bookings_count += 1
        coolie.daily_earnings += booking.total_fare
        coolie.save(update_fields=['total_bookings_count', 'daily_earnings'])
        Notification.objects.create(
            recipient=booking.passenger,
            title="Service Completed! Please Rate Your Coolie ⭐",
            message=f"Your luggage service is complete. Please leave a rating and review for {coolie.user.get_full_name()}.",
            notification_type='BOOKING',
            link_url=f"/bookings/track/{booking.booking_id}/"
        )
        notify_booking_completed(booking)
        messages.success(request, f"Great job! Booking {booking.booking_id} marked as completed. Total fare: ₹{booking.total_fare}")

    else:
        messages.error(request, "Invalid action or booking is not in the correct state for this action.")

    return redirect('coolies:dashboard')
