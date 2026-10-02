from django.shortcuts import render, get_object_or_404
from rest_framework import viewsets, permissions
from rest_framework.response import Response
from rest_framework.decorators import action

from .models import Station, Platform, Facility
from .serializers import StationSerializer, PlatformSerializer, FacilitySerializer


# --- HTML Views ---

def station_list_view(request):
    """
    List of active stations with search and facility badges.
    """
    query = request.GET.get('q', '').strip()
    stations = Station.objects.filter(is_active=True)
    if query:
        stations = stations.filter(name__icontains=query) | stations.filter(code__icontains=query) | stations.filter(city__icontains=query)

    return render(request, 'stations/station_list.html', {
        'stations': stations,
        'query': query
    })


def station_detail_view(request, code):
    """
    Comprehensive station profile page with platforms, facilities, and live map container.
    """
    station = get_object_or_404(Station, code__iexact=code)
    platforms = station.platforms.all()
    facilities = station.facilities.all()

    # Categorize facilities
    categories = {}
    for f in facilities:
        cat = f.get_facility_type_display()
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(f)

    return render(request, 'stations/station_detail.html', {
        'station': station,
        'platforms': platforms,
        'facilities': facilities,
        'categories': categories,
    })


# --- REST API ViewSets ---

class StationViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Station.objects.filter(is_active=True)
    serializer_class = StationSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = 'code'

    @action(detail=True, methods=['get'])
    def map_data(self, request, code=None):
        station = self.get_object()
        facilities = FacilitySerializer(station.facilities.filter(is_operational=True), many=True).data
        platforms = PlatformSerializer(station.platforms.all(), many=True).data
        return Response({
            'station': {
                'id': station.id,
                'name': station.name,
                'code': station.code,
                'latitude': float(station.latitude),
                'longitude': float(station.longitude),
            },
            'platforms': platforms,
            'facilities': facilities
        })


class PlatformViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Platform.objects.all()
    serializer_class = PlatformSerializer
    permission_classes = [permissions.AllowAny]


class FacilityViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Facility.objects.all()
    serializer_class = FacilitySerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        qs = super().get_queryset()
        station_code = self.request.query_params.get('station')
        f_type = self.request.query_params.get('type')
        if station_code:
            qs = qs.filter(station__code__iexact=station_code)
        if f_type:
            qs = qs.filter(facility_type=f_type)
        return qs
