"""
RailSaathi URL Configuration
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from accounts.views import landing_view
from analytics.views import AnalyticsDataAPIView

urlpatterns = [
    path('admin/', admin.site.urls),

    # Main Landing Homepage
    path('', landing_view, name='landing'),

    # Modular App URLs
    path('accounts/', include('accounts.urls', namespace='accounts')),
    path('stations/', include('stations.urls', namespace='stations')),
    path('coolies/', include('coolies.urls', namespace='coolies')),
    path('bookings/', include('bookings.urls', namespace='bookings')),
    path('assistance/', include('assistance.urls', namespace='assistance')),
    path('lost-found/', include('lost_found.urls', namespace='lost_found')),
    path('complaints/', include('complaints.urls', namespace='complaints')),
    path('reviews/', include('reviews.urls', namespace='reviews')),
    path('notifications/', include('notifications.urls', namespace='notifications')),
    path('portal/', include('analytics.urls', namespace='admin_portal')),

    # REST APIs
    path('api/v1/', include('config.api_router')),
    path('api/v1/analytics-data/', AnalyticsDataAPIView.as_view(), name='api_analytics_charts'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
