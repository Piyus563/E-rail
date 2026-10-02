from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard_redirect, name='dashboard_redirect'),
    path('passenger/dashboard/', views.passenger_dashboard, name='passenger_dashboard'),
    path('notifications/', views.notifications_view, name='notifications'),
    path('assistant/chat/', views.assistant_chat_api, name='assistant_chat'),
    path('assistant/recommendations/', views.coolie_recommendations_api, name='coolie_recommendations'),
]
