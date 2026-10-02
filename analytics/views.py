from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Count, Sum, Avg
from django.utils import timezone
from datetime import timedelta
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions

from accounts.models import User, PassengerProfile, CoolieProfile
from stations.models import Station, Platform, Facility
from bookings.models import Booking
from assistance.models import AssistanceRequest
from lost_found.models import LostFoundReport
from complaints.models import Complaint
from reviews.models import Review


def is_admin_check(user):
    return user.is_authenticated and (user.role == 'ADMIN' or user.is_superuser)


@login_required
@user_passes_test(is_admin_check, login_url='accounts:login')
def admin_dashboard_view(request):
    """
    Executive Admin Dashboard with KPIs, Charts, and Recent Activities.
    """
    now = timezone.now()
    seven_days_ago = now - timedelta(days=7)

    # Core Metric Cards
    total_passengers = User.objects.filter(role='PASSENGER').count()
    total_coolies = CoolieProfile.objects.count()
    online_coolies = CoolieProfile.objects.filter(is_online=True).count()
    active_bookings = Booking.objects.filter(status__in=['REQUESTED', 'ACCEPTED', 'SERVICE_STARTED']).count()
    completed_bookings = Booking.objects.filter(status='COMPLETED').count()
    pending_assistance = AssistanceRequest.objects.filter(status__in=['PENDING', 'ASSIGNED']).count()
    unresolved_complaints = Complaint.objects.exclude(status__in=['RESOLVED', 'REJECTED']).count()
    total_revenue = Booking.objects.filter(status='COMPLETED').aggregate(Sum('total_fare'))['total_fare__sum'] or 0

    # Recent Records
    recent_bookings = Booking.objects.all().order_by('-created_at')[:8]
    recent_assistance = AssistanceRequest.objects.all().order_by('-created_at')[:5]
    recent_complaints = Complaint.objects.all().order_by('-created_at')[:5]
    recent_coolies = CoolieProfile.objects.all().order_by('-rating')[:5]

    context = {
        'total_passengers': total_passengers,
        'total_coolies': total_coolies,
        'online_coolies': online_coolies,
        'active_bookings': active_bookings,
        'completed_bookings': completed_bookings,
        'pending_assistance': pending_assistance,
        'unresolved_complaints': unresolved_complaints,
        'total_revenue': total_revenue,
        'recent_bookings': recent_bookings,
        'recent_assistance': recent_assistance,
        'recent_complaints': recent_complaints,
        'recent_coolies': recent_coolies,
    }
    return render(request, 'admin_portal/dashboard.html', context)


@login_required
@user_passes_test(is_admin_check, login_url='accounts:login')
def admin_manage_passengers(request):
    passengers = User.objects.filter(role='PASSENGER').order_by('-date_joined')
    return render(request, 'admin_portal/passengers.html', {'passengers': passengers})


@login_required
@user_passes_test(is_admin_check, login_url='accounts:login')
def admin_manage_coolies(request):
    coolies = CoolieProfile.objects.all().order_by('-rating')
    if request.method == 'POST':
        coolie_id = request.POST.get('coolie_id')
        action_type = request.POST.get('action')
        coolie = get_object_or_404(CoolieProfile, id=coolie_id)
        if action_type == 'toggle_verify':
            coolie.is_verified = not coolie.is_verified
            coolie.save(update_fields=['is_verified'])
            messages.success(request, f"Coolie {coolie.badge_number} verification status updated.")
        elif action_type == 'toggle_online':
            coolie.is_online = not coolie.is_online
            coolie.save(update_fields=['is_online'])
            messages.success(request, f"Coolie {coolie.badge_number} online status updated.")
        return redirect('admin_portal:coolies')

    return render(request, 'admin_portal/coolies.html', {'coolies': coolies})


@login_required
@user_passes_test(is_admin_check, login_url='accounts:login')
def admin_manage_bookings(request):
    status_filter = request.GET.get('status', '')
    bookings = Booking.objects.all().order_by('-created_at')
    if status_filter:
        bookings = bookings.filter(status=status_filter)

    if request.method == 'POST':
        booking_id = request.POST.get('booking_id')
        new_status = request.POST.get('new_status')
        bkg = get_object_or_404(Booking, booking_id=booking_id)
        bkg.status = new_status
        if new_status == 'COMPLETED':
            bkg.completed_at = timezone.now()
        bkg.save()
        messages.success(request, f"Booking #{bkg.booking_id} status changed to {new_status}.")
        return redirect('admin_portal:bookings')

    return render(request, 'admin_portal/bookings.html', {
        'bookings': bookings,
        'status_filter': status_filter,
        'statuses': Booking.STATUS_CHOICES,
    })


@login_required
@user_passes_test(is_admin_check, login_url='accounts:login')
def admin_manage_stations(request):
    stations = Station.objects.all().order_by('name')
    return render(request, 'admin_portal/stations.html', {'stations': stations})


@login_required
@user_passes_test(is_admin_check, login_url='accounts:login')
def admin_manage_assistance(request):
    requests = AssistanceRequest.objects.all().order_by('-created_at')

    if request.method == 'POST':
        req_id = request.POST.get('request_id')
        new_status = request.POST.get('status')
        staff_name = request.POST.get('assigned_staff_name', '').strip()
        staff_phone = request.POST.get('assigned_staff_phone', '').strip()

        ast_req = get_object_or_404(AssistanceRequest, request_id=req_id)
        ast_req.status = new_status
        if staff_name:
            ast_req.assigned_staff_name = staff_name
        if staff_phone:
            ast_req.assigned_staff_phone = staff_phone
        if new_status == 'RESOLVED':
            ast_req.resolved_at = timezone.now()
        ast_req.save()
        messages.success(request, f"Assistance request #{ast_req.request_id} updated.")
        return redirect('admin_portal:assistance')

    return render(request, 'admin_portal/assistance.html', {
        'requests': requests,
        'statuses': AssistanceRequest.STATUS_CHOICES,
    })


@login_required
@user_passes_test(is_admin_check, login_url='accounts:login')
def admin_manage_lost_found(request):
    reports = LostFoundReport.objects.all().order_by('-created_at')

    if request.method == 'POST':
        report_id = request.POST.get('report_id')
        new_status = request.POST.get('status')
        notes = request.POST.get('admin_notes', '').strip()

        lf = get_object_or_404(LostFoundReport, report_id=report_id)
        lf.status = new_status
        if notes:
            lf.admin_notes = notes
        lf.save()
        messages.success(request, f"Lost & Found Report #{lf.report_id} updated.")
        return redirect('admin_portal:lost_found')

    return render(request, 'admin_portal/lost_found.html', {
        'reports': reports,
        'statuses': LostFoundReport.STATUS_CHOICES,
    })


@login_required
@user_passes_test(is_admin_check, login_url='accounts:login')
def admin_manage_complaints(request):
    complaints = Complaint.objects.all().order_by('-created_at')

    if request.method == 'POST':
        ticket_id = request.POST.get('ticket_id')
        new_status = request.POST.get('status')
        officer = request.POST.get('assigned_officer', '').strip()
        notes = request.POST.get('resolution_notes', '').strip()

        cmp = get_object_or_404(Complaint, ticket_id=ticket_id)
        cmp.status = new_status
        if officer:
            cmp.assigned_officer = officer
        if notes:
            cmp.resolution_notes = notes
        if new_status == 'RESOLVED':
            cmp.resolved_at = timezone.now()
        cmp.save()
        messages.success(request, f"Grievance Ticket #{cmp.ticket_id} updated.")
        return redirect('admin_portal:complaints')

    return render(request, 'admin_portal/complaints.html', {
        'complaints': complaints,
        'statuses': Complaint.STATUS_CHOICES,
    })


@login_required
@user_passes_test(is_admin_check, login_url='accounts:login')
def admin_manage_reviews(request):
    reviews = Review.objects.all().order_by('-created_at')
    return render(request, 'admin_portal/reviews.html', {'reviews': reviews})


# --- REST API Analytics Endpoint for Chart.js ---

class AnalyticsDataAPIView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        now = timezone.now()

        # 1. Daily Bookings for Last 7 Days
        daily_labels = []
        daily_counts = []
        for i in range(6, -1, -1):
            day = (now - timedelta(days=i)).date()
            daily_labels.append(day.strftime('%a, %d %b'))
            count = Booking.objects.filter(created_at__date=day).count()
            daily_counts.append(count)

        # 2. Booking Status Distribution
        status_dist = Booking.objects.values('status').annotate(count=Count('status'))
        status_labels = [item['status'] for item in status_dist]
        status_data = [item['count'] for item in status_dist]

        # 3. Assistance Types Breakdown
        assist_dist = AssistanceRequest.objects.values('assistance_type').annotate(count=Count('assistance_type'))
        assist_labels = [dict(AssistanceRequest.ASSISTANCE_TYPES).get(item['assistance_type'], item['assistance_type']) for item in assist_dist]
        assist_data = [item['count'] for item in assist_dist]

        # 4. Station Demands
        station_dist = Booking.objects.values('station__name').annotate(count=Count('station'))
        stn_labels = [item['station__name'] or 'General' for item in station_dist]
        stn_data = [item['count'] for item in station_dist]

        return Response({
            'daily_bookings': {
                'labels': daily_labels,
                'data': daily_counts,
            },
            'booking_status': {
                'labels': status_labels,
                'data': status_data,
            },
            'assistance_types': {
                'labels': assist_labels,
                'data': assist_data,
            },
            'station_demand': {
                'labels': stn_labels,
                'data': stn_data,
            }
        })
