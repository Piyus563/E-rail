from django.urls import path
from . import views

app_name = 'complaints'

urlpatterns = [
    path('', views.complaint_submit_view, name='submit'),
    path('list/', views.complaint_list_view, name='list'),
    path('ticket/<str:ticket_id>/', views.complaint_detail_view, name='detail'),
]
