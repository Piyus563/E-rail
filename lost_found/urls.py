from django.urls import path
from . import views

app_name = 'lost_found'

urlpatterns = [
    path('', views.lost_found_index_view, name='index'),
    path('report/<str:report_id>/', views.lost_found_detail_view, name='detail'),
]
