from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from rest_framework import viewsets, permissions

from .models import LostFoundReport
from .serializers import LostFoundReportSerializer
from stations.models import Station, Platform


def lost_found_index_view(request):
    """
    Lost & Found Hub with two tabs ('I Lost Something', 'I Found Something') + Browse Public Listings.
    """
    stations = Station.objects.filter(is_active=True)
    filter_type = request.GET.get('type', '')
    filter_category = request.GET.get('category', '')
    query = request.GET.get('q', '').strip()

    reports = LostFoundReport.objects.exclude(status='CLOSED')

    if filter_type:
        reports = reports.filter(report_type=filter_type)
    if filter_category:
        reports = reports.filter(category=filter_category)
    if query:
        reports = reports.filter(item_name__icontains=query) | reports.filter(description__icontains=query)

    if request.method == 'POST':
        report_type = request.POST.get('report_type', 'LOST')
        item_name = request.POST.get('item_name', '').strip()
        category = request.POST.get('category', 'OTHER')
        description = request.POST.get('description', '').strip()
        station_id = request.POST.get('station_id')
        platform_id = request.POST.get('platform_id')
        coach_number = request.POST.get('coach_number', '').strip()
        contact_name = request.POST.get('contact_name', '').strip()
        contact_phone = request.POST.get('contact_phone', '').strip()
        contact_email = request.POST.get('contact_email', '').strip()
        image = request.FILES.get('image')

        stn_obj = get_object_or_404(Station, id=station_id)
        plat_obj = Platform.objects.filter(id=platform_id).first() if platform_id else None

        report = LostFoundReport.objects.create(
            user=request.user if request.user.is_authenticated else None,
            report_type=report_type,
            item_name=item_name,
            category=category,
            description=description,
            station=stn_obj,
            platform=plat_obj,
            coach_number=coach_number,
            contact_name=contact_name,
            contact_phone=contact_phone,
            contact_email=contact_email,
            image=image,
            status='REPORTED'
        )

        messages.success(request, f"Your {report.get_report_type_display()} report has been registered (Ref #{report.report_id})! Station authorities will review it.")
        return redirect('lost_found:detail', report_id=report.report_id)

    return render(request, 'lost_found/index.html', {
        'stations': stations,
        'reports': reports,
        'categories': LostFoundReport.CATEGORY_CHOICES,
        'filter_type': filter_type,
        'filter_category': filter_category,
        'query': query,
    })


def lost_found_detail_view(request, report_id):
    """
    Detailed tracking of a Lost / Found Report.
    """
    report = get_object_or_404(LostFoundReport, report_id=report_id)
    return render(request, 'lost_found/detail.html', {'report': report})


# --- REST API ViewSet ---

class LostFoundViewSet(viewsets.ModelViewSet):
    queryset = LostFoundReport.objects.all()
    serializer_class = LostFoundReportSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        qs = super().get_queryset()
        r_type = self.request.query_params.get('type')
        if r_type:
            qs = qs.filter(report_type=r_type)
        return qs

    def perform_create(self, serializer):
        serializer.save(user=self.request.user if self.request.user.is_authenticated else None)
