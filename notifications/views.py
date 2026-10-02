from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from rest_framework import viewsets, permissions

from .models import Notification
from .serializers import NotificationSerializer


@login_required
def mark_notification_read(request, pk):
    notif = get_object_or_404(Notification, pk=pk, recipient=request.user)
    notif.is_read = True
    notif.save(update_fields=['is_read'])
    if notif.link_url:
        return redirect(notif.link_url)
    return redirect('accounts:notifications')


@login_required
def unread_count_api(request):
    """Returns unread notification count as JSON for live badge polling."""
    count = Notification.objects.filter(recipient=request.user, is_read=False).count()
    return JsonResponse({'unread_count': count})


# --- REST API ViewSet ---

class NotificationViewSet(viewsets.ModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user)
