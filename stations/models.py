from django.db import models


class Station(models.Model):
    name = models.CharField(max_length=150, help_text="Station Full Name (e.g. New Jalpaiguri Junction)")
    code = models.CharField(max_length=10, unique=True, help_text="Station Code (e.g. NJP)")
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    number_of_platforms = models.PositiveIntegerField(default=5)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, default=26.6853)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, default=88.4418)
    image = models.ImageField(upload_to='stations/', null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.code})"


class Platform(models.Model):
    station = models.ForeignKey(Station, on_delete=models.CASCADE, related_name='platforms')
    number = models.PositiveIntegerField()
    description = models.CharField(max_length=200, blank=True, help_text="e.g. Main lines, Rajdhani/Vande Bharat berth")
    has_lift = models.BooleanField(default=True)
    has_escalator = models.BooleanField(default=True)
    has_wheelchair_ramp = models.BooleanField(default=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    class Meta:
        ordering = ['station', 'number']
        unique_together = ('station', 'number')

    def __str__(self):
        return f"{self.station.code} - Platform {self.number}"


class Facility(models.Model):
    FACILITY_TYPES = [
        ('WASHROOM', '🚻 Washroom / Restroom'),
        ('DRINKING_WATER', '💧 Clean Drinking Water'),
        ('LIFT', '🛗 Passenger Lift / Elevator'),
        ('ESCALATOR', '🚶 Escalator'),
        ('FOOD', '🍴 Food Court & Refreshments'),
        ('WAITING_ROOM', '🪑 AC & General Waiting Room'),
        ('PARKING', '🚗 Station Parking Area'),
        ('MEDICAL', '🏥 Emergency Medical Room'),
        ('HELP_DESK', 'ℹ️ Sahayata / Help Desk'),
        ('CLOAK_ROOM', '🛅 Cloak Room & Luggage Locker'),
        ('WHEELCHAIR_POINT', '♿ Wheelchair Pick-up Hub'),
    ]

    station = models.ForeignKey(Station, on_delete=models.CASCADE, related_name='facilities')
    platform = models.ForeignKey(Platform, on_delete=models.SET_NULL, null=True, blank=True, related_name='facilities')
    facility_type = models.CharField(max_length=30, choices=FACILITY_TYPES)
    name = models.CharField(max_length=150)
    location_description = models.CharField(max_length=255, help_text="e.g. Near FOB 1, Platform 1 Center")
    latitude = models.DecimalField(max_digits=9, decimal_places=6, default=26.6853)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, default=88.4418)
    is_operational = models.BooleanField(default=True)
    contact_number = models.CharField(max_length=20, blank=True)
    icon = models.CharField(max_length=50, default='fa-info-circle')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'Facilities'
        ordering = ['station', 'facility_type']

    def __str__(self):
        return f"{self.name} - {self.station.code}"
