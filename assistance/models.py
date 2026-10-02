import uuid
from django.db import models


def generate_assistance_id():
    return f"RS-AST-{uuid.uuid4().hex[:6].upper()}"


class AssistanceRequest(models.Model):
    ASSISTANCE_TYPES = [
        ('WHEELCHAIR', '♿ Wheelchair Assistance'),
        ('SENIOR_CITIZEN', '👴 Senior Citizen Assistance'),
        ('FAMILY_CHILD', '👨‍👩‍👧 Family & Child Care Assistance'),
        ('LUGGAGE', '🧳 Luggage Transit Help'),
        ('MEDICAL_EMERGENCY', '🏥 Medical First Aid Assistance'),
        ('GENERAL_HELP', '🙋 General Station Help & Guidance'),
    ]

    STATUS_CHOICES = [
        ('PENDING', 'Pending Assignment'),
        ('ASSIGNED', 'Staff Assigned'),
        ('IN_PROGRESS', 'Assistance In Progress'),
        ('RESOLVED', 'Completed / Resolved'),
        ('CANCELLED', 'Cancelled'),
    ]

    request_id = models.CharField(max_length=30, unique=True, default=generate_assistance_id)
    passenger = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='assistance_requests')
    passenger_name = models.CharField(max_length=150)
    passenger_phone = models.CharField(max_length=20)
    station = models.ForeignKey('stations.Station', on_delete=models.CASCADE, related_name='assistance_requests')
    platform = models.ForeignKey('stations.Platform', on_delete=models.SET_NULL, null=True, blank=True, related_name='assistance_requests')
    coach_number = models.CharField(max_length=30, blank=True, help_text="e.g. S3, B4, General")
    train_number = models.CharField(max_length=50, blank=True, help_text="e.g. 12345 Saraighat Express")

    assistance_type = models.CharField(max_length=30, choices=ASSISTANCE_TYPES, default='WHEELCHAIR')
    description = models.TextField(help_text="Provide any specific details (e.g. need ramp access, unable to climb stairs)")

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    assigned_staff_name = models.CharField(max_length=150, blank=True)
    assigned_staff_phone = models.CharField(max_length=20, blank=True)
    staff_notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.request_id} - {self.get_assistance_type_display()} ({self.passenger_name})"
