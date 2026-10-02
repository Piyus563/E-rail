from decimal import Decimal
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta

from accounts.models import User, PassengerProfile, CoolieProfile
from stations.models import Station, Platform, Facility
from bookings.models import Booking
from assistance.models import AssistanceRequest
from lost_found.models import LostFoundReport
from complaints.models import Complaint
from reviews.models import Review, StationReview
from notifications.models import Notification


class Command(BaseCommand):
    help = 'Seeds realistic demo data for RailSaathi (NJP Station, Coolies, Bookings, Requests, etc.)'

    def handle(self, *args, **options):
        self.stdout.write("Starting RailSaathi seed data generation...")

        # 1. Create or Get Station (New Jalpaiguri Junction - NJP)
        station, created = Station.objects.get_or_create(
            code='NJP',
            defaults={
                'name': 'New Jalpaiguri Junction',
                'city': 'Siliguri',
                'state': 'West Bengal',
                'number_of_platforms': 5,
                'latitude': Decimal('26.685300'),
                'longitude': Decimal('88.441800'),
                'is_active': True,
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f"Created Station: {station}"))

        # Secondary Station: Howrah Junction (HWH) for multi-station demo
        hwh_station, _ = Station.objects.get_or_create(
            code='HWH',
            defaults={
                'name': 'Howrah Junction',
                'city': 'Kolkata',
                'state': 'West Bengal',
                'number_of_platforms': 23,
                'latitude': Decimal('22.583800'),
                'longitude': Decimal('88.342600'),
                'is_active': True,
            }
        )

        # 2. Create Platforms for NJP
        platforms = []
        platform_data = [
            (1, "Main Broad Gauge & Vande Bharat/Rajdhani Berth", True, True, True, Decimal('26.685350'), Decimal('88.441850')),
            (2, "Express & Superfast Line", True, True, True, Decimal('26.685450'), Decimal('88.442000')),
            (3, "Mail & Intercity Express Line", True, False, True, Decimal('26.685550'), Decimal('88.442150')),
            (4, "Passenger & Express Transit Line", False, False, True, Decimal('26.685650'), Decimal('88.442300')),
            (5, "Darjeeling Himalayan Railway (DHR) & Heritage Line", False, False, True, Decimal('26.685750'), Decimal('88.442450')),
        ]
        for num, desc, lift, esc, ramp, lat, lon in platform_data:
            plat, _ = Platform.objects.get_or_create(
                station=station,
                number=num,
                defaults={
                    'description': desc,
                    'has_lift': lift,
                    'has_escalator': esc,
                    'has_wheelchair_ramp': ramp,
                    'latitude': lat,
                    'longitude': lon,
                }
            )
            platforms.append(plat)

        # 3. Create Facilities for NJP
        facility_list = [
            ('WASHROOM', 'Executive & Divyangjan Restroom', 'Platform 1 Center, adjacent to AC Waiting Hall', Decimal('26.685320'), Decimal('88.441810'), platforms[0]),
            ('WASHROOM', 'General Public Washroom', 'Platform 2 & 3 Foot-Over Bridge Junction', Decimal('26.685500'), Decimal('88.442050'), platforms[1]),
            ('DRINKING_WATER', 'RO Purified Drinking Water Booth', 'Platform 1 near Coach B4 position', Decimal('26.685380'), Decimal('88.441890'), platforms[0]),
            ('DRINKING_WATER', 'Cold Water Kiosk', 'Platform 2 near Coach S2 position', Decimal('26.685470'), Decimal('88.442020'), platforms[1]),
            ('LIFT', 'Glass Passenger Elevator (FOB 1)', 'Platform 1 & 2 Escalator link', Decimal('26.685400'), Decimal('88.441920'), platforms[0]),
            ('ESCALATOR', 'Up/Down Heavy-Duty Escalator', 'Platform 1 Main Portico to FOB', Decimal('26.685340'), Decimal('88.441830'), platforms[0]),
            ('FOOD', 'IRCTC Food Plaza & Jan Aahaar', 'Platform 1 Concourse Area', Decimal('26.685280'), Decimal('88.441750'), platforms[0]),
            ('WAITING_ROOM', 'Air Conditioned Executive Lounge', 'Platform 1 First Floor', Decimal('26.685310'), Decimal('88.441790'), platforms[0]),
            ('WAITING_ROOM', 'Ladies & Senior Citizen Waiting Hall', 'Platform 1 East Wing', Decimal('26.685360'), Decimal('88.441870'), platforms[0]),
            ('PARKING', '24x7 Multi-Vehicle Car & Cab Parking', 'Station Front Circulating Plaza', Decimal('26.685150'), Decimal('88.441600'), None),
            ('MEDICAL', '24x7 Railway Emergency Medical Health Post', 'Platform 1 near RPF Assistance Post', Decimal('26.685420'), Decimal('88.441940'), platforms[0]),
            ('HELP_DESK', 'Rail Sahayata Information & Tourist Desk', 'Main Concourse Entry Hall', Decimal('26.685250'), Decimal('88.441700'), None),
            ('CLOAK_ROOM', 'Electronic Luggage Cloak Room & Lockers', 'Platform 1 West End', Decimal('26.685290'), Decimal('88.441730'), platforms[0]),
            ('WHEELCHAIR_POINT', 'Divyangjan & Senior Citizen Assistance Hub', 'Main Station Porch Entry Gate 1', Decimal('26.685200'), Decimal('88.441650'), None),
        ]

        for f_type, name, loc, lat, lon, plat in facility_list:
            Facility.objects.get_or_create(
                station=station,
                name=name,
                defaults={
                    'facility_type': f_type,
                    'location_description': loc,
                    'latitude': lat,
                    'longitude': lon,
                    'platform': plat,
                    'is_operational': True,
                    'contact_number': '139',
                }
            )

        # 4. Create Users: Admin, Passenger, Coolies
        # Admin User
        admin_user, _ = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@railsaathi.com',
                'first_name': 'Station',
                'last_name': 'Master',
                'role': 'ADMIN',
                'phone': '+91 9999900001',
                'is_staff': True,
                'is_superuser': True,
            }
        )
        admin_user.set_password('admin123')
        admin_user.save()

        # Passenger User
        passenger_user, _ = User.objects.get_or_create(
            username='priya_singh',
            defaults={
                'email': 'passenger@railsaathi.com',
                'first_name': 'Priya',
                'last_name': 'Singh',
                'role': 'PASSENGER',
                'phone': '+91 9876543210',
            }
        )
        passenger_user.set_password('pass123')
        passenger_user.save()
        PassengerProfile.objects.get_or_create(
            user=passenger_user,
            defaults={'emergency_contact': '+91 9876543211', 'preferred_language': 'English'}
        )

        # Additional Passenger for reviews & bookings
        passenger2, _ = User.objects.get_or_create(
            username='arjun_verma',
            defaults={
                'email': 'arjun@gmail.com',
                'first_name': 'Arjun',
                'last_name': 'Verma',
                'role': 'PASSENGER',
                'phone': '+91 9811223344',
            }
        )
        passenger2.set_password('pass123')
        passenger2.save()
        PassengerProfile.objects.get_or_create(
            user=passenger2,
            defaults={'emergency_contact': '+91 9811223345', 'preferred_language': 'Hindi'}
        )

        # Coolies Data (5 Realistic Licensed Sahayaks)
        coolie_specs = [
            ('ramesh_kumar', 'ramesh@railsaathi.com', 'Ramesh', 'Kumar', '+91 9871110001', 'NJP-C-104', 6, Decimal('4.90'), 48, True, platforms[0], Decimal('1250.00'), 154, 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=300&fit=crop&crop=face'),
            ('suresh_sah', 'suresh@railsaathi.com', 'Suresh', 'Sahani', '+91 9871110002', 'NJP-C-108', 4, Decimal('4.80'), 36, True, platforms[1], Decimal('980.00'), 98, 'https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=300&fit=crop&crop=face'),
            ('manoj_yadav', 'manoj@railsaathi.com', 'Manoj', 'Yadav', '+91 9871110003', 'NJP-C-112', 8, Decimal('4.95'), 72, True, platforms[0], Decimal('1600.00'), 240, 'https://images.unsplash.com/photo-1492562080023-ab3db95bfbce?w=300&fit=crop&crop=face'),
            ('rajesh_sharma', 'rajesh@railsaathi.com', 'Rajesh', 'Sharma', '+91 9871110004', 'NJP-C-120', 3, Decimal('4.70'), 22, True, platforms[2], Decimal('650.00'), 55, 'https://images.unsplash.com/photo-1506794778202-cad84cf45f1d?w=300&fit=crop&crop=face'),
            ('anil_das', 'anil@railsaathi.com', 'Anil', 'Das', '+91 9871110005', 'NJP-C-135', 5, Decimal('4.85'), 40, False, platforms[3], Decimal('0.00'), 112, 'https://images.unsplash.com/photo-1522075469751-3a6694fb2f61?w=300&fit=crop&crop=face'),
        ]

        coolie_profiles = []
        for uname, email, fname, lname, phone, badge, exp, rating, rat_count, online, plat, earn, total_bkg, photo in coolie_specs:
            user_obj, _ = User.objects.get_or_create(
                username=uname,
                defaults={
                    'email': email,
                    'first_name': fname,
                    'last_name': lname,
                    'role': 'COOLIE',
                    'phone': phone,
                }
            )
            user_obj.set_password('coolie123')
            user_obj.save()

            cp, _ = CoolieProfile.objects.get_or_create(
                user=user_obj,
                defaults={
                    'badge_number': badge,
                    'station': station,
                    'experience_years': exp,
                    'rating': rating,
                    'total_ratings_count': rat_count,
                    'is_verified': True,
                    'is_online': online,
                    'current_platform': plat,
                    'daily_earnings': earn,
                    'total_bookings_count': total_bkg,
                    'photo_url': photo,
                }
            )
            coolie_profiles.append(cp)

        # 5. Create Demo Bookings
        now = timezone.now()

        # Active Booking (Accepted by Ramesh Kumar for Priya Singh)
        bkg1, _ = Booking.objects.get_or_create(
            booking_id='RS-BKG-A1092',
            defaults={
                'passenger': passenger_user,
                'coolie': coolie_profiles[0],  # Ramesh
                'station': station,
                'platform': platforms[0],
                'journey_type': 'ARRIVAL',
                'train_number': '12042',
                'train_name': 'New Jalpaiguri - Howrah Shatabdi Express',
                'coach_number': 'C2',
                'seat_number': '34',
                'luggage_type': 'TROLLEY',
                'number_of_bags': 2,
                'approx_weight_kg': 28,
                'meeting_point': 'Platform 1 near Coach C2 De-boarding Door',
                'scheduled_time': now + timedelta(minutes=45),
                'base_fare': Decimal('100.00'),
                'extra_bag_fare': Decimal('50.00'),
                'total_fare': Decimal('150.00'),
                'status': 'ACCEPTED',
                'accepted_at': now - timedelta(minutes=10),
            }
        )

        # Completed Booking with Review
        bkg2, _ = Booking.objects.get_or_create(
            booking_id='RS-BKG-C8821',
            defaults={
                'passenger': passenger_user,
                'coolie': coolie_profiles[0],  # Ramesh
                'station': station,
                'platform': platforms[1],
                'journey_type': 'DEPARTURE',
                'train_number': '22302',
                'train_name': 'Vande Bharat Express',
                'coach_number': 'E1',
                'seat_number': '12',
                'luggage_type': 'HEAVY_BAGS',
                'number_of_bags': 3,
                'approx_weight_kg': 35,
                'meeting_point': 'Station Main Porch VIP Drop-off Gate',
                'scheduled_time': now - timedelta(days=2),
                'base_fare': Decimal('100.00'),
                'extra_bag_fare': Decimal('100.00'),
                'total_fare': Decimal('200.00'),
                'status': 'COMPLETED',
                'accepted_at': now - timedelta(days=2, hours=1),
                'started_at': now - timedelta(days=2, minutes=50),
                'completed_at': now - timedelta(days=2, minutes=15),
            }
        )
        Review.objects.get_or_create(
            booking=bkg2,
            defaults={
                'passenger': passenger_user,
                'coolie': coolie_profiles[0],
                'rating': 5,
                'punctuality_rating': 5,
                'behavior_rating': 5,
                'comment': 'Ramesh ji was waiting right at the car gate and handled all heavy bags very carefully. Very polite and disciplined!',
            }
        )

        # Second completed booking for Arjun Verma -> Manoj Yadav
        bkg3, _ = Booking.objects.get_or_create(
            booking_id='RS-BKG-M5504',
            defaults={
                'passenger': passenger2,
                'coolie': coolie_profiles[2],  # Manoj
                'station': station,
                'platform': platforms[0],
                'journey_type': 'ARRIVAL',
                'train_number': '12344',
                'train_name': 'Padatik Express',
                'coach_number': 'B1',
                'seat_number': '48',
                'luggage_type': 'COMBINED',
                'number_of_bags': 4,
                'approx_weight_kg': 45,
                'meeting_point': 'Platform 1 Coach B1',
                'scheduled_time': now - timedelta(days=1),
                'base_fare': Decimal('100.00'),
                'extra_bag_fare': Decimal('150.00'),
                'total_fare': Decimal('250.00'),
                'status': 'COMPLETED',
                'accepted_at': now - timedelta(days=1, hours=2),
                'started_at': now - timedelta(days=1, hours=1, minutes=45),
                'completed_at': now - timedelta(days=1, hours=1, minutes=10),
            }
        )
        Review.objects.get_or_create(
            booking=bkg3,
            defaults={
                'passenger': passenger2,
                'coolie': coolie_profiles[2],
                'rating': 5,
                'punctuality_rating': 5,
                'behavior_rating': 5,
                'comment': 'Super fast assistance! Manoj Yadav guided my elderly parents safely to the taxi stand.',
            }
        )

        # 6. Create Demo Assistance Requests
        AssistanceRequest.objects.get_or_create(
            request_id='RS-AST-W0012',
            defaults={
                'passenger': passenger_user,
                'passenger_name': 'Priya Singh (for grandmother Mrs. Usha Singh)',
                'passenger_phone': '+91 9876543210',
                'station': station,
                'platform': platforms[0],
                'coach_number': 'B3',
                'train_number': '12377 Padatik Express',
                'assistance_type': 'WHEELCHAIR',
                'description': 'Need wheelchair assistance from de-boarding at Platform 1 to Station Main Exit cab parking. Passenger has knee mobility limitation.',
                'status': 'ASSIGNED',
                'assigned_staff_name': 'Subhash Roy (Sahayata Attendant #12)',
                'assigned_staff_phone': '+91 9832299881',
                'staff_notes': 'Wheelchair positioned at Platform 1 Help Desk.',
            }
        )

        AssistanceRequest.objects.get_or_create(
            request_id='RS-AST-S0045',
            defaults={
                'passenger': passenger2,
                'passenger_name': 'Arjun Verma',
                'passenger_phone': '+91 9811223344',
                'station': station,
                'platform': platforms[1],
                'coach_number': 'S4',
                'train_number': '15960 Kamrup Express',
                'assistance_type': 'SENIOR_CITIZEN',
                'description': 'Senior citizen couple needing assistance to locate connecting train on Platform 3 and navigating the foot overbridge.',
                'status': 'IN_PROGRESS',
                'assigned_staff_name': 'Pankaj Barman (Duty Sahayak)',
                'assigned_staff_phone': '+91 9832299884',
            }
        )

        # 7. Create Demo Lost & Found Reports
        LostFoundReport.objects.get_or_create(
            report_id='RS-LF-L9041',
            defaults={
                'user': passenger_user,
                'report_type': 'LOST',
                'item_name': 'Navy Blue American Tourister Laptop Backpack',
                'category': 'ELECTRONICS',
                'description': 'Contains Lenovo ThinkPad laptop, charger, noise cancelling headphones, and railway ID badge in front pocket.',
                'station': station,
                'platform': platforms[0],
                'coach_number': 'Coach C2 berth area',
                'incident_date': now - timedelta(hours=5),
                'contact_name': 'Priya Singh',
                'contact_phone': '+91 9876543210',
                'contact_email': 'passenger@railsaathi.com',
                'status': 'UNDER_VERIFICATION',
                'admin_notes': 'RPF security checking CCTV footage around Coach C2 at 11:30 AM arrival.',
            }
        )

        LostFoundReport.objects.get_or_create(
            report_id='RS-LF-F3012',
            defaults={
                'user': None,
                'report_type': 'FOUND',
                'item_name': 'Titan Regalia Men Wristwatch (Gold & Silver Strap)',
                'category': 'VALUABLES',
                'description': 'Found resting on seating sofa inside Platform 1 AC Waiting Lounge.',
                'station': station,
                'platform': platforms[0],
                'incident_date': now - timedelta(days=1),
                'contact_name': 'Station Master Duty Office (NJP)',
                'contact_phone': '0353-2698222',
                'status': 'REPORTED',
                'storage_location': 'Station Master Locker Safe #4',
                'admin_notes': 'Owner can verify with serial number or purchase invoice to claim.',
            }
        )

        # 8. Create Demo Complaints
        Complaint.objects.get_or_create(
            ticket_id='RS-CMP-T8810',
            defaults={
                'user': passenger_user,
                'category': 'CLEANLINESS',
                'station': station,
                'platform': platforms[2],
                'description': 'Waste bin overflowing near Coach S5 position on Platform 3. Needs immediate sanitation attention before evening express arrival.',
                'contact_name': 'Priya Singh',
                'contact_phone': '+91 9876543210',
                'contact_email': 'passenger@railsaathi.com',
                'priority': 'MEDIUM',
                'status': 'IN_PROGRESS',
                'assigned_officer': 'Deepak Majumdar (Station Sanitation Inspector)',
                'resolution_notes': 'Housekeeping team dispatched with mechanized cleaning cart.',
            }
        )

        Complaint.objects.get_or_create(
            ticket_id='RS-CMP-T5521',
            defaults={
                'user': passenger2,
                'category': 'DEFECTIVE_FACILITY',
                'station': station,
                'platform': platforms[0],
                'description': 'Water dispenser tap #2 was leaking on Platform 1 near escalators.',
                'contact_name': 'Arjun Verma',
                'contact_phone': '+91 9811223344',
                'contact_email': 'arjun@gmail.com',
                'priority': 'LOW',
                'status': 'RESOLVED',
                'assigned_officer': 'Engineering Maintenance Dept',
                'resolution_notes': 'Valve replaced by station plumbing crew at 09:15 AM today.',
                'resolved_at': now - timedelta(hours=3),
            }
        )

        # 9. Create Notifications
        Notification.objects.get_or_create(
            recipient=passenger_user,
            title="Coolie Confirmed Your Booking!",
            defaults={
                'message': "Sahayak Ramesh Kumar (Badge #NJP-C-104) accepted your booking RS-BKG-A1092 at Platform 1.",
                'notification_type': 'BOOKING',
                'link_url': '/bookings/track/RS-BKG-A1092/',
                'is_read': False,
            }
        )

        Notification.objects.get_or_create(
            recipient=coolie_profiles[0].user,
            title="New Booking Request Assigned",
            defaults={
                'message': "Passenger Priya Singh requested luggage assistance at Platform 1 Coach C2 (Train 12042).",
                'notification_type': 'BOOKING',
                'link_url': '/coolies/dashboard/',
                'is_read': False,
            }
        )

        # 10. Station Reviews
        StationReview.objects.get_or_create(
            station=station,
            passenger=passenger_user,
            defaults={
                'rating': 5,
                'cleanliness_rating': 5,
                'amenities_rating': 5,
                'comment': 'New Jalpaiguri station has undergone amazing upgrades. The lifts, wide platforms, and helpful coolies made our journey delightful!',
            }
        )

        self.stdout.write(self.style.SUCCESS("[OK] Seed data created successfully for RailSaathi!"))
        self.stdout.write("==================================================")
        self.stdout.write("DEMO ACCOUNTS READY FOR TESTING:")
        self.stdout.write("1. Admin:     admin@railsaathi.com    / admin123 (username: admin)")
        self.stdout.write("2. Passenger: passenger@railsaathi.com / pass123 (username: priya_singh)")
        self.stdout.write("3. Coolie:    ramesh@railsaathi.com   / coolie123 (username: ramesh_kumar)")
        self.stdout.write("4. Coolie:    suresh@railsaathi.com   / coolie123 (username: suresh_sah)")
        self.stdout.write("5. Coolie:    manoj@railsaathi.com    / coolie123 (username: manoj_yadav)")
        self.stdout.write("==================================================")
