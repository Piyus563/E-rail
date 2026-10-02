from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from rest_framework import viewsets, permissions

from .models import Complaint
from .serializers import ComplaintSerializer
from stations.models import Station, Platform


def complaint_submit_view(request):
    """
    Passenger Complaint & Grievance Lodging Portal.
    """
    stations = Station.objects.filter(is_active=True)
    default_station = stations.first()
    platforms = default_station.platforms.all() if default_station else []

    if request.method == 'POST':
        category = request.POST.get('category', 'CLEANLINESS')
        station_id = request.POST.get('station_id')
        platform_id = request.POST.get('platform_id')
        description = request.POST.get('description', '').strip()
        contact_name = request.POST.get('contact_name', '').strip()
        contact_phone = request.POST.get('contact_phone', '').strip()
        contact_email = request.POST.get('contact_email', '').strip()
        priority = request.POST.get('priority', 'MEDIUM')
        image = request.FILES.get('image')

        stn_obj = get_object_or_404(Station, id=station_id)
        plat_obj = Platform.objects.filter(id=platform_id).first() if platform_id else None

        complaint = Complaint.objects.create(
            user=request.user if request.user.is_authenticated else None,
            category=category,
            station=stn_obj,
            platform=plat_obj,
            description=description,
            contact_name=contact_name,
            contact_phone=contact_phone,
            contact_email=contact_email,
            priority=priority,
            image=image,
            status='NEW'
        )

        messages.success(request, f"Grievance registered successfully! Your Ticket ID is: {complaint.ticket_id}. Station team notified.")
        return redirect('complaints:detail', ticket_id=complaint.ticket_id)

    return render(request, 'complaints/submit_form.html', {
        'stations': stations,
        'default_station': default_station,
        'platforms': platforms,
        'categories': Complaint.CATEGORY_CHOICES,
        'priorities': Complaint.PRIORITY_CHOICES,
    })


def complaint_detail_view(request, ticket_id):
    """
    Live Status View of a Complaint Ticket.
    """
    complaint = get_object_or_404(Complaint, ticket_id=ticket_id)
    return render(request, 'complaints/detail.html', {'complaint': complaint})


def complaint_list_view(request):
    """
    List user complaints.
    """
    complaints = []
    if request.user.is_authenticated:
        complaints = Complaint.objects.filter(user=request.user)
    return render(request, 'complaints/list.html', {'complaints': complaints})


# --- REST API ViewSet ---

class ComplaintViewSet(viewsets.ModelViewSet):
    queryset = Complaint.objects.all()
    serializer_class = ComplaintSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if not user.is_authenticated:
            # Unauthenticated users can only list (read-only enforced by permission class)
            return qs.none()
        if user.role == 'ADMIN' or user.is_superuser:
            return qs
        return qs.filter(user=user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user if self.request.user.is_authenticated else None)
