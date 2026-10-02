from django.urls import path
from . import views

app_name = 'admin_portal'

urlpatterns = [
    path('dashboard/', views.admin_dashboard_view, name='dashboard'),
    path('passengers/', views.admin_manage_passengers, name='passengers'),
    path('coolies/', views.admin_manage_coolies, name='coolies'),
    path('bookings/', views.admin_manage_bookings, name='bookings'),
    path('stations/', views.admin_manage_stations, name='stations'),
    path('assistance/', views.admin_manage_assistance, name='assistance'),
    path('lost-found/', views.admin_manage_lost_found, name='lost_found'),
    path('complaints/', views.admin_manage_complaints, name='complaints'),
    path('reviews/', views.admin_manage_reviews, name='reviews'),
    path('api/charts-data/', views.AnalyticsDataAPIView.as_view(), name='api_charts_data'),

]
