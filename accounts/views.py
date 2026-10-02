from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import action

from .models import User, PassengerProfile, CoolieProfile, AuditLog
from .serializers import UserSerializer, PassengerProfileSerializer, CoolieProfileSerializer
from stations.models import Station
from bookings.models import Booking
from assistance.models import AssistanceRequest
from lost_found.models import LostFoundReport
from complaints.models import Complaint
from notifications.models import Notification
from .ai import assistant_reply, recommend_coolies


# --- HTML Template Views ---

def landing_view(request):
    """
    Landing Homepage for RailSaathi with hero, live station list, features, and quick book.
    """
    stations = Station.objects.filter(is_active=True)
    njp_station = Station.objects.filter(code='NJP').first() or stations.first()
    recent_coolies = CoolieProfile.objects.filter(is_online=True, is_verified=True)[:4]

    context = {
        'stations': stations,
        'default_station': njp_station,
        'coolies': recent_coolies,
        'stats': {
            'stations_count': stations.count(),
            'coolies_count': CoolieProfile.objects.filter(is_verified=True).count(),
            'bookings_count': Booking.objects.count(),
        }
    }
    return render(request, 'landing.html', context)


def login_view(request):
    """
    Custom login view with role redirection.
    """
    if request.user.is_authenticated:
        return redirect('accounts:dashboard_redirect')

    if request.method == 'POST':
        identifier = request.POST.get('username_or_email', '').strip()
        password = request.POST.get('password', '')

        user = None
        if '@' in identifier:
            user_obj = User.objects.filter(email__iexact=identifier).first()
            if user_obj:
                user = authenticate(request, username=user_obj.username, password=password)
        else:
            user = authenticate(request, username=identifier, password=password)

        if user is not None:
            login(request, user)
            messages.success(request, f"Welcome back, {user.first_name or user.username}!")
            # Prevent open redirect: only allow relative paths
            next_url = request.POST.get('next', '').strip()
            if next_url and next_url.startswith('/'):
                return redirect(next_url)
            return redirect('accounts:dashboard_redirect')
        else:
            messages.error(request, "Invalid username/email or password.")

    return render(request, 'accounts/login.html')


def register_view(request):
    """
    Unified registration view supporting Passenger or Coolie sign-up.
    """
    if request.user.is_authenticated:
        return redirect('accounts:dashboard_redirect')

    stations = Station.objects.filter(is_active=True)

    if request.method == 'POST':
        role = request.POST.get('role', 'PASSENGER')
        if role not in ('PASSENGER', 'COOLIE'):
            role = 'PASSENGER'
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        username = request.POST.get('username', '').strip() or email.split('@')[0]
        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_password', '')

        if not (email and password and first_name):
            messages.error(request, "Please fill in all required fields.")
            return render(request, 'accounts/register.html', {'stations': stations})

        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return render(request, 'accounts/register.html', {'stations': stations})

        if len(password) < 8:
            messages.error(request, "Password must be at least 8 characters long.")
            return render(request, 'accounts/register.html', {'stations': stations})

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists. Please choose another.")
            return render(request, 'accounts/register.html', {'stations': stations})

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already registered. Please login.")
            return render(request, 'accounts/register.html', {'stations': stations})

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            phone=phone or None,
            role=role
        )

        if role == 'PASSENGER':
            PassengerProfile.objects.create(user=user)
        elif role == 'COOLIE':
            station_id = request.POST.get('station')
            badge = request.POST.get('badge_number', '').strip() or f"NJP-C-{user.id + 200}"
            station = Station.objects.filter(id=station_id).first() if station_id else None
            # Ensure badge uniqueness
            if CoolieProfile.objects.filter(badge_number=badge).exists():
                badge = f"{badge}-{user.id}"
            CoolieProfile.objects.create(
                user=user,
                badge_number=badge,
                station=station,
                is_verified=True,
                is_online=True
            )

        login(request, user)
        messages.success(request, "Account created successfully! Welcome to RailSaathi.")
        return redirect('accounts:dashboard_redirect')

    return render(request, 'accounts/register.html', {'stations': stations})


def logout_view(request):
    """Logout requires POST to prevent CSRF-via-GET logout attacks."""
    if request.method == 'POST':
        logout(request)
        messages.info(request, "You have been logged out safely.")
    return redirect('landing')


@login_required
def dashboard_redirect(request):
    """
    Intelligent redirect based on user role.
    """
    if request.user.role == 'ADMIN' or request.user.is_superuser:
        return redirect('admin_portal:dashboard')
    elif request.user.role == 'COOLIE':
        return redirect('coolies:dashboard')
    else:
        return redirect('accounts:passenger_dashboard')


@login_required
def passenger_dashboard(request):
    """
    Passenger Dashboard showing quick actions, active bookings, history, assistance requests.
    """
    user = request.user
    active_booking = Booking.objects.filter(
        passenger=user,
        status__in=['REQUESTED', 'ACCEPTED', 'SERVICE_STARTED']
    ).first()

    recent_bookings = Booking.objects.filter(passenger=user).exclude(id=active_booking.id if active_booking else None)[:5]
    my_assistance = AssistanceRequest.objects.filter(passenger=user)[:4]
    my_lost_found = LostFoundReport.objects.filter(user=user)[:4]
    my_complaints = Complaint.objects.filter(user=user)[:4]

    default_station = Station.objects.filter(code='NJP').first() or Station.objects.first()

    context = {
        'user': user,
        'active_booking': active_booking,
        'recent_bookings': recent_bookings,
        'my_assistance': my_assistance,
        'my_lost_found': my_lost_found,
        'my_complaints': my_complaints,
        'default_station': default_station,
        'all_stations': Station.objects.filter(is_active=True),
    }
    return render(request, 'passenger/dashboard.html', context)


@login_required
def notifications_view(request):
    """
    Notifications list page. Mark all as read via POST only.
    """
    if request.method == 'POST' and request.POST.get('mark_all_read'):
        Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
        messages.success(request, "All notifications marked as read.")
        return redirect('accounts:notifications')

    notifications = Notification.objects.filter(recipient=request.user)
    unread_count = notifications.filter(is_read=False).count()
    return render(request, 'accounts/notifications.html', {
        'notifications': notifications,
        'unread_count': unread_count,
    })


@login_required
@require_POST
def assistant_chat_api(request):
    """Small, local station-help assistant with no external API dependency."""
    message = request.POST.get('message', '').strip()
    if not message:
        return JsonResponse({'error': 'Message is required.'}, status=400)
    return JsonResponse({'reply': assistant_reply(message)})


@login_required
def coolie_recommendations_api(request):
    """Rank live NJP coolies for the booking wizard and mobile clients."""
    station_code = request.GET.get('station', 'NJP')
    try:
        number_of_bags = max(1, int(request.GET.get('bags', 1)))
    except (TypeError, ValueError):
        number_of_bags = 1
    needs_assistance = request.GET.get('assistance', '').lower() in ('1', 'true', 'yes')
    return JsonResponse({
        'station': station_code.upper(),
        'recommendations': recommend_coolies(station_code, number_of_bags, needs_assistance),
    })


# --- REST API ViewSets ---

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def get_permissions(self):
        if self.action in ['create']:
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    @action(detail=False, methods=['get'])
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)


class CoolieProfileViewSet(viewsets.ModelViewSet):
    queryset = CoolieProfile.objects.filter(is_verified=True)
    serializer_class = CoolieProfileSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        qs = super().get_queryset()
        station_code = self.request.query_params.get('station_code')
        online_only = self.request.query_params.get('online')

        if station_code:
            qs = qs.filter(station__code__iexact=station_code)
        if online_only == 'true':
            qs = qs.filter(is_online=True)
        return qs

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def toggle_status(self, request, pk=None):
        coolie = self.get_object()
        if request.user != coolie.user and not (request.user.role == 'ADMIN' or request.user.is_superuser):
            return Response({'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)

        coolie.is_online = not coolie.is_online
        coolie.save(update_fields=['is_online'])
        return Response({'status': 'success', 'is_online': coolie.is_online})
