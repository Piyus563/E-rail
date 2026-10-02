from django.db import models


class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('BOOKING', '🧳 Booking Alert'),
        ('ASSISTANCE', '♿ Assistance Update'),
        ('LOST_FOUND', '🔎 Lost & Found Match'),
        ('COMPLAINT', '📢 Complaint Update'),
        ('SYSTEM', '🔔 System Notice'),
    ]

    recipient = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=150)
    message = models.TextField()
    notification_type = models.CharField(max_length=30, choices=NOTIFICATION_TYPES, default='SYSTEM')
    link_url = models.CharField(max_length=255, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.recipient.username} - {self.title}"
