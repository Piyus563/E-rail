from django.urls import path
from . import views

app_name = 'bookings'

urlpatterns = [
    path('book/', views.book_coolie_view, name='book_coolie'),
    path('track/<str:booking_id>/', views.booking_tracking_view, name='tracking'),
    path('history/', views.booking_history_view, name='history'),
]
