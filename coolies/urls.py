from django.urls import path
from . import views

app_name = 'coolies'

urlpatterns = [
    path('', views.coolie_list_view, name='coolie_list'),
    path('dashboard/', views.coolie_dashboard_view, name='dashboard'),
    path('profile/<int:pk>/', views.coolie_detail_view, name='coolie_detail'),
    path('action/<str:booking_id>/<str:action>/', views.update_booking_status, name='update_booking_status'),
]
