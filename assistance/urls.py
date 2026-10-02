from django.urls import path
from . import views

app_name = 'assistance'

urlpatterns = [
    path('', views.assistance_request_view, name='request'),
    path('list/', views.assistance_list_view, name='list'),
    path('status/<str:request_id>/', views.assistance_detail_view, name='detail'),
]
