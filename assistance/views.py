from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from rest_framework import viewsets, permissions
from rest_framework.response import Response

from .models import AssistanceRequest
from .serializers import AssistanceRequestSerializer
from stations.models import Station, Platform
from notifications.models import Notification


def assistance_request_view(request):
    """
    Passenger Assistance Request Page (Wheelchair, Senior Citizen, Family/Child, Medical, General Help).
    """
    stations = Station.objects.filter(is_active=True)
    default_station = stations.first()
    platforms = default_station.platforms.all() if default_station else []

    if request.method == 'POST':
        passenger_name = request.POST.get('passenger_name', '').strip()
        passenger_phone = request.POST.get('passenger_phone', '').strip()
        station_id = request.POST.get('station_id')
        platform_id = request.POST.get('platform_id')
        coach_number = request.POST.get('coach_number', '').strip()
        train_number = request.POST.get('train_number', '').strip()
        assistance_type = request.POST.get('assistance_type', 'WHEELCHAIR')
        description = request.POST.get('description', '').strip()

        stn_obj = get_object_or_404(Station, id=station_id)
        plat_obj = Platform.objects.filter(id=platform_id).first() if platform_id else None

        req = AssistanceRequest.objects.create(
            passenger=request.user if request.user.is_authenticated else None,
            passenger_name=passenger_name,
            passenger_phone=passenger_phone,
            station=stn_obj,
            platform=plat_obj,
            coach_number=coach_number,
            train_number=train_number,
            assistance_type=assistance_type,
            description=description,
            status='PENDING'
        )

        messages.success(request, f"Assistance Request Submitted Successfully! Your Request ID is: {req.request_id}")
        return redirect('assistance:detail', request_id=req.request_id)

    return render(request, 'assistance/request_form.html', {
        'stations': stations,
        'default_station': default_station,
        'platforms': platforms,
    })


def assistance_detail_view(request, request_id):
    """
    Live Status View for Passenger Assistance with Progress Timeline.
    """
    assistance_req = get_object_or_404(AssistanceRequest, request_id=request_id)
    return render(request, 'assistance/detail.html', {'req': assistance_req})


def assistance_list_view(request):
    """
    List of assistance requests for user or public tracking.
    """
    if request.user.is_authenticated:
        requests = AssistanceRequest.objects.filter(passenger=request.user).order_by('-created_at')
    else:
        requests = []
    return render(request, 'assistance/list.html', {'requests': requests})


# --- REST API ViewSet ---

class AssistanceRequestViewSet(viewsets.ModelViewSet):
    queryset = AssistanceRequest.objects.all()
    serializer_class = AssistanceRequestSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        qs = super().get_queryset()
        station_code = self.request.query_params.get('station')
        if station_code:
            qs = qs.filter(station__code__iexact=station_code)
        user = self.request.user
        if not user.is_authenticated:
            return qs.none()
        if user.role == 'ADMIN' or user.is_superuser:
            return qs
        return qs.filter(passenger=user)

    def perform_create(self, serializer):
        serializer.save(passenger=self.request.user if self.request.user.is_authenticated else None)
