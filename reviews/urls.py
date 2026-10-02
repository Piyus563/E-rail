from django.urls import path
from . import views

app_name = 'reviews'

urlpatterns = [
    path('submit/<str:booking_id>/', views.submit_review_view, name='submit'),
]
