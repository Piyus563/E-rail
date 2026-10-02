from notifications.models import Notification
from stations.models import Station


def user_roles_context(request):
    """
    Context processor to inject current user role helpers, unread notifications count,
    and active station into all templates.
    """
    # Single query for stations — evaluated once, passed to templates
    active_stations = list(Station.objects.filter(is_active=True)[:10])

    context = {
        'is_passenger': False,
        'is_coolie': False,
        'is_station_admin': False,
        'unread_notifications_count': 0,
        'all_stations': active_stations,
    }

    if request.user.is_authenticated:
        context['is_passenger'] = request.user.role == 'PASSENGER'
        context['is_coolie'] = request.user.role == 'COOLIE'
        context['is_station_admin'] = request.user.role == 'ADMIN' or request.user.is_superuser
        try:
            context['unread_notifications_count'] = Notification.objects.filter(
                recipient=request.user, is_read=False
            ).count()
        except Exception:
            context['unread_notifications_count'] = 0

    return context
