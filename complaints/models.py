import uuid
from django.db import models


def generate_complaint_id():
    return f"RS-CMP-{uuid.uuid4().hex[:6].upper()}"


class Complaint(models.Model):
    CATEGORY_CHOICES = [
        ('CLEANLINESS', '🧹 Station / Platform Cleanliness Issue'),
        ('COOLIE_OVERCHARGING', '🧳 Coolie Overcharging / Misbehavior'),
        ('DEFECTIVE_FACILITY', '🛗 Broken Lift / Escalator / Washroom'),
        ('STAFF_BEHAVIOR', '👮 Station Staff / Porter Misconduct'),
        ('SAFETY_SECURITY', '🛡️ Safety & Security Concern'),
        ('DRINKING_WATER', '💧 Water Dispenser Empty / Dirty'),
        ('FOOD_QUALITY', '🍴 Overpricing / Poor Food Hygiene'),
        ('OTHER', '📢 Other Railway Grievances'),
    ]

    PRIORITY_CHOICES = [
        ('LOW', 'Low Priority'),
        ('MEDIUM', 'Medium Priority'),
        ('HIGH', 'High Priority'),
        ('URGENT', '🚨 Urgent / Emergency'),
    ]

    STATUS_CHOICES = [
        ('NEW', 'New Grievance Submitted'),
        ('ASSIGNED', 'Assigned to Railway Officer'),
        ('IN_PROGRESS', 'Investigation in Progress'),
        ('RESOLVED', 'Issue Resolved'),
        ('REJECTED', 'Dismissed / Inapplicable'),
    ]

    ticket_id = models.CharField(max_length=30, unique=True, default=generate_complaint_id)
    user = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='complaints')
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES, default='CLEANLINESS')
    station = models.ForeignKey('stations.Station', on_delete=models.CASCADE, related_name='complaints')
    platform = models.ForeignKey('stations.Platform', on_delete=models.SET_NULL, null=True, blank=True, related_name='complaints')
    description = models.TextField(help_text="Explain the problem in detail with specific locations or porter badge numbers if applicable")

    image = models.ImageField(upload_to='complaints/', null=True, blank=True)
    image_url = models.CharField(max_length=500, blank=True)

    contact_name = models.CharField(max_length=150)
    contact_phone = models.CharField(max_length=20)
    contact_email = models.EmailField(blank=True)

    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='MEDIUM')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='NEW')

    assigned_officer = models.CharField(max_length=150, blank=True)
    resolution_notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.ticket_id} - {self.get_category_display()} ({self.status})"
