from rest_framework.routers import DefaultRouter
from accounts.views import UserViewSet, CoolieProfileViewSet
from stations.views import StationViewSet, PlatformViewSet, FacilityViewSet
from bookings.views import BookingViewSet
from assistance.views import AssistanceRequestViewSet
from lost_found.views import LostFoundViewSet
from complaints.views import ComplaintViewSet
from reviews.views import ReviewViewSet, StationReviewViewSet
from notifications.views import NotificationViewSet

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='api_users')
router.register(r'coolies', CoolieProfileViewSet, basename='api_coolies')
router.register(r'stations', StationViewSet, basename='api_stations')
router.register(r'platforms', PlatformViewSet, basename='api_platforms')
router.register(r'facilities', FacilityViewSet, basename='api_facilities')
router.register(r'bookings', BookingViewSet, basename='api_bookings')
router.register(r'assistance', AssistanceRequestViewSet, basename='api_assistance')
router.register(r'lost-found', LostFoundViewSet, basename='api_lost_found')
router.register(r'complaints', ComplaintViewSet, basename='api_complaints')
router.register(r'reviews', ReviewViewSet, basename='api_reviews')
router.register(r'station-reviews', StationReviewViewSet, basename='api_station_reviews')
router.register(r'notifications', NotificationViewSet, basename='api_notifications')

urlpatterns = router.urls
