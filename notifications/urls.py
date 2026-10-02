from django.urls import path
from . import views

app_name = 'notifications'

urlpatterns = [
    path('read/<int:pk>/', views.mark_notification_read, name='mark_read'),
    path('unread-count/', views.unread_count_api, name='unread_count'),
]
