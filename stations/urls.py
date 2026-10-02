from django.urls import path
from . import views

app_name = 'stations'

urlpatterns = [
    path('', views.station_list_view, name='station_list'),
    path('<str:code>/', views.station_detail_view, name='station_detail'),
]
