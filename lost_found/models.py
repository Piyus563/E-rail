import uuid
from django.db import models
from django.utils import timezone


def generate_lost_found_id():
    return f"RS-LF-{uuid.uuid4().hex[:6].upper()}"


class LostFoundReport(models.Model):
    REPORT_TYPES = [
        ('LOST', '❌ I Lost Something'),
        ('FOUND', '✅ I Found Something'),
    ]

    CATEGORY_CHOICES = [
        ('ELECTRONICS', '📱 Mobile / Laptop / Electronics'),
        ('LUGGAGE_BAG', '🧳 Luggage / Backpack / Handbag'),
        ('WALLET_DOCS', '💳 Wallet / ID Cards / Documents'),
        ('VALUABLES', '💍 Jewelry / Watch / Valuables'),
        ('CLOTHING', '🧥 Jackets / Clothing / Accessories'),
        ('KEYS', '🔑 Keys / Essentials'),
        ('OTHER', '📦 Other Items'),
    ]

    STATUS_CHOICES = [
        ('REPORTED', 'Report Submitted'),
        ('UNDER_VERIFICATION', 'Under Verification by Station Master'),
        ('MATCHED', 'Potential Match Found'),
        ('CLAIMED', 'Claimed by Owner'),
        ('RESOLVED', 'Resolved & Handed Over'),
        ('CLOSED', 'Closed / Unclaimed'),
    ]

    report_id = models.CharField(max_length=30, unique=True, default=generate_lost_found_id)
    user = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='lost_found_reports')
    report_type = models.CharField(max_length=10, choices=REPORT_TYPES, default='LOST')
    item_name = models.CharField(max_length=150, help_text="e.g. Black Lenovo ThinkPad Laptop Bag")
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES, default='LUGGAGE_BAG')
    description = models.TextField(help_text="Detailed physical description, stickers, brand, color, unique marks")
    image = models.ImageField(upload_to='lost_found/', null=True, blank=True)
    image_url = models.CharField(max_length=500, blank=True, help_text="Fallback image URL for demo")

    station = models.ForeignKey('stations.Station', on_delete=models.CASCADE, related_name='lost_found_reports')
    platform = models.ForeignKey('stations.Platform', on_delete=models.SET_NULL, null=True, blank=True, related_name='lost_found_reports')
    coach_number = models.CharField(max_length=30, blank=True, help_text="e.g. A1 Berth 23")
    incident_date = models.DateTimeField(default=timezone.now)

    contact_name = models.CharField(max_length=150)
    contact_phone = models.CharField(max_length=20)
    contact_email = models.EmailField(blank=True)

    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='REPORTED')
    storage_location = models.CharField(max_length=200, blank=True, help_text="e.g. Station Master Office Locker B")
    admin_notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.report_id} - [{self.get_report_type_display()}] {self.item_name}"
