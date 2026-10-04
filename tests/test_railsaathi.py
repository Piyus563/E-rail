from decimal import Decimal
from django.test import TestCase, Client, override_settings
from django.urls import reverse, NoReverseMatch
from django.utils import timezone

from accounts.models import User, PassengerProfile, CoolieProfile
from stations.models import Station, Platform, Facility
from bookings.models import Booking
from assistance.models import AssistanceRequest
from lost_found.models import LostFoundReport
from complaints.models import Complaint
from reviews.models import Review


class RailSaathiCoreTests(TestCase):
    def test_seed_accounts_have_no_default_passwords_in_production(self):
        from accounts.management.commands.seed_data import _set_seed_password

        new_user = User(username='new_seed_user')
        existing_user = User(username='existing_seed_user')
        existing_user.set_password('admin123')

        with override_settings(DEBUG=False):
            _set_seed_password(new_user, 'admin123', created=True)
            _set_seed_password(existing_user, 'admin123', created=False)

        self.assertFalse(new_user.has_usable_password())
        self.assertFalse(existing_user.has_usable_password())

    def test_station_map_routes_removed(self):
        """The app should no longer expose interactive station map routes."""
        with self.assertRaises(NoReverseMatch):
            reverse('stations:station_map_default')

        with self.assertRaises(NoReverseMatch):
            reverse('stations:station_map', args=['NJP'])

    def setUp(self):
        self.client = Client()
        Station.objects.filter(code='NJP').delete()

        # Create Station & Platform
        self.station = Station.objects.create(
            name="New Jalpaiguri Junction",
            code="NJP",
            city="Siliguri",
            state="West Bengal",
            number_of_platforms=5,
            latitude=Decimal('26.6853'),
            longitude=Decimal('88.4418')
        )
        self.platform1 = Platform.objects.create(
            station=self.station,
            number=1,
            description="Main Line",
            has_lift=True,
            has_escalator=True
        )

        # Create Admin
        self.admin_user = User.objects.create_superuser(
            username="admin_test",
            email="admin@test.com",
            password="adminpassword",
            role="ADMIN"
        )

        # Create Passenger
        self.passenger_user = User.objects.create_user(
            username="passenger_test",
            email="passenger@test.com",
            password="passpassword",
            first_name="Priya",
            last_name="Singh",
            role="PASSENGER",
            phone="+91 9876543210"
        )
        self.passenger_profile = PassengerProfile.objects.create(user=self.passenger_user)

        # Create Coolie
        self.coolie_user = User.objects.create_user(
            username="coolie_test",
            email="coolie@test.com",
            password="cooliepassword",
            first_name="Ramesh",
            last_name="Kumar",
            role="COOLIE",
            phone="+91 9871110001"
        )
        self.coolie_profile = CoolieProfile.objects.create(
            user=self.coolie_user,
            badge_number="NJP-C-104",
            station=self.station,
            experience_years=5,
            is_verified=True,
            is_online=True
        )

    def test_01_user_roles_and_authentication(self):
        """Test authentication and role separation"""
        self.assertTrue(self.passenger_user.is_passenger())
        self.assertTrue(self.coolie_user.is_coolie())
        self.assertTrue(self.admin_user.is_station_admin())

        # Test login
        logged_in = self.client.login(username="passenger_test", password="passpassword")
        self.assertTrue(logged_in)
        response = self.client.get(reverse('accounts:passenger_dashboard'))
        self.assertEqual(response.status_code, 200)

    def test_02_coolie_availability_toggle(self):
        """Test coolie going online and offline"""
        self.client.login(username="coolie_test", password="cooliepassword")
        self.assertTrue(self.coolie_profile.is_online)

        # Post toggle
        response = self.client.post(reverse('coolies:dashboard'), {'toggle_status': '1'})
        self.assertEqual(response.status_code, 302)
        self.coolie_profile.refresh_from_db()
        self.assertFalse(self.coolie_profile.is_online)

    def test_03_booking_creation_and_fare_calculation(self):
        """Test booking creation with dynamic fare calculation (Base 100 + 50/extra bag)"""
        self.client.login(username="passenger_test", password="passpassword")

        # 3 bags => 100 + 2*50 = 200
        response = self.client.post(reverse('bookings:book_coolie'), {
            'station_id': self.station.id,
            'platform_id': self.platform1.id,
            'coolie_id': self.coolie_profile.id,
            'journey_type': 'ARRIVAL',
            'train_number': '12042 Shatabdi',
            'coach_number': 'C2',
            'luggage_type': 'TROLLEY',
            'number_of_bags': 3,
            'approx_weight_kg': 30,
            'meeting_point': 'Platform 1 Coach C2 Door',
        })
        self.assertEqual(response.status_code, 302)

        booking = Booking.objects.filter(passenger=self.passenger_user).first()
        self.assertIsNotNone(booking)
        self.assertEqual(booking.status, 'REQUESTED')
        self.assertEqual(booking.total_fare, Decimal('200.00'))

    def test_04_coolie_booking_workflow_state_transitions(self):
        """Test full state machine: REQUESTED -> ACCEPTED -> SERVICE_STARTED -> COMPLETED"""
        booking = Booking.objects.create(
            passenger=self.passenger_user,
            coolie=self.coolie_profile,
            station=self.station,
            platform=self.platform1,
            number_of_bags=2,
            total_fare=Decimal('150.00'),
            status='REQUESTED'
        )

        self.client.login(username="coolie_test", password="cooliepassword")

        # Accept — must be POST (GET is blocked after security fix)
        resp1 = self.client.post(reverse('coolies:update_booking_status', args=[booking.booking_id, 'accept']))
        self.assertEqual(resp1.status_code, 302)
        booking.refresh_from_db()
        self.assertEqual(booking.status, 'ACCEPTED')

        # Start Service
        resp2 = self.client.post(reverse('coolies:update_booking_status', args=[booking.booking_id, 'start']))
        self.assertEqual(resp2.status_code, 302)
        booking.refresh_from_db()
        self.assertEqual(booking.status, 'SERVICE_STARTED')

        # Complete Service
        resp3 = self.client.post(reverse('coolies:update_booking_status', args=[booking.booking_id, 'complete']))
        self.assertEqual(resp3.status_code, 302)
        booking.refresh_from_db()
        self.assertEqual(booking.status, 'COMPLETED')

    def test_05_rating_and_review_recalculation(self):
        """Test passenger leaving star rating & coolie aggregate rating update"""
        booking = Booking.objects.create(
            passenger=self.passenger_user,
            coolie=self.coolie_profile,
            station=self.station,
            platform=self.platform1,
            status='COMPLETED'
        )

        self.client.login(username="passenger_test", password="passpassword")
        response = self.client.post(reverse('bookings:tracking', args=[booking.booking_id]), {
            'submit_review': '1',
            'rating': 5,
            'punctuality_rating': 5,
            'behavior_rating': 5,
            'comment': 'Exceptional service and timely help!'
        })
        self.assertEqual(response.status_code, 302)

        review = Review.objects.filter(booking=booking).first()
        self.assertIsNotNone(review)
        self.assertEqual(review.rating, 5)

        self.coolie_profile.refresh_from_db()
        self.assertEqual(float(self.coolie_profile.rating), 5.0)

    def test_06_assistance_request(self):
        """Test passenger requesting assistance"""
        response = self.client.post(reverse('assistance:request'), {
            'assistance_type': 'WHEELCHAIR',
            'passenger_name': 'Mrs. Usha Singh',
            'passenger_phone': '+91 9876543210',
            'station_id': self.station.id,
            'platform_id': self.platform1.id,
            'description': 'Need wheelchair at coach door',
        })
        self.assertEqual(response.status_code, 302)
        req = AssistanceRequest.objects.filter(passenger_name='Mrs. Usha Singh').first()
        self.assertIsNotNone(req)
        self.assertTrue(req.request_id.startswith('RS-AST-'))

    def test_07_lost_and_found_submission(self):
        """Test lost & found reporting"""
        response = self.client.post(reverse('lost_found:index'), {
            'report_type': 'LOST',
            'item_name': 'Black HP Laptop Bag',
            'category': 'ELECTRONICS',
            'station_id': self.station.id,
            'platform_id': self.platform1.id,
            'description': 'Left inside waiting room',
            'contact_name': 'Priya Singh',
            'contact_phone': '+91 9876543210',
        })
        self.assertEqual(response.status_code, 302)
        lf = LostFoundReport.objects.filter(item_name='Black HP Laptop Bag').first()
        self.assertIsNotNone(lf)
        self.assertTrue(lf.report_id.startswith('RS-LF-'))

    def test_08_complaint_registration(self):
        """Test complaint submission"""
        response = self.client.post(reverse('complaints:submit'), {
            'category': 'CLEANLINESS',
            'station_id': self.station.id,
            'platform_id': self.platform1.id,
            'priority': 'MEDIUM',
            'description': 'Overflowing dustbin on platform',
            'contact_name': 'Priya Singh',
            'contact_phone': '+91 9876543210',
        })
        self.assertEqual(response.status_code, 302)
        cmp = Complaint.objects.filter(contact_name='Priya Singh').first()
        self.assertIsNotNone(cmp)
        self.assertTrue(cmp.ticket_id.startswith('RS-CMP-'))

    def test_09_drf_api_endpoints(self):
        """Test REST API endpoints"""
        # Test public stations API
        resp = self.client.get('/api/v1/stations/')
        self.assertEqual(resp.status_code, 200)

        # Test public coolies API
        resp_coolies = self.client.get('/api/v1/coolies/')
        self.assertEqual(resp_coolies.status_code, 200)

        # Analytics chart API requires admin
        self.client.login(username="admin_test", password="adminpassword")
        resp_charts = self.client.get('/portal/api/charts-data/')
        self.assertEqual(resp_charts.status_code, 200)
        self.assertIn('daily_bookings', resp_charts.json())
        self.client.logout()

        # Analytics chart API blocked for unauthenticated users
        resp_unauth = self.client.get('/portal/api/charts-data/')
        self.assertIn(resp_unauth.status_code, [403, 401])

    def test_10_ai_assistant_and_recommendations(self):
        self.client.login(username="passenger_test", password="passpassword")

        chat_response = self.client.post(reverse('accounts:assistant_chat'), {'message': 'What is the coolie fare?'})
        self.assertEqual(chat_response.status_code, 200)
        self.assertIn('Rs. 100', chat_response.json()['reply'])

        recommendation_response = self.client.get(reverse('accounts:coolie_recommendations'), {
            'station': 'NJP', 'bags': 4, 'assistance': 'true'
        })
        self.assertEqual(recommendation_response.status_code, 200)
        recommendations = recommendation_response.json()['recommendations']
        self.assertEqual(recommendations[0]['badge_number'], 'NJP-C-104')
        self.assertIn('experienced', recommendations[0]['reason'])

    def test_11_ai_endpoints_require_authentication(self):
        chat_response = self.client.post(reverse('accounts:assistant_chat'), {'message': 'map'})
        recommendation_response = self.client.get(reverse('accounts:coolie_recommendations'))
        self.assertEqual(chat_response.status_code, 302)
        self.assertEqual(recommendation_response.status_code, 302)


    def test_12_booking_input_validation(self):
        """Test that invalid number_of_bags and approx_weight_kg are clamped safely"""
        self.client.login(username="passenger_test", password="passpassword")

        # Send negative bags and garbage weight — should not crash
        response = self.client.post(reverse('bookings:book_coolie'), {
            'station_id': self.station.id,
            'platform_id': self.platform1.id,
            'coolie_id': self.coolie_profile.id,
            'journey_type': 'ARRIVAL',
            'luggage_type': 'TROLLEY',
            'number_of_bags': '-5',       # should clamp to 1
            'approx_weight_kg': 'abc',    # should fallback to 20
        })
        self.assertEqual(response.status_code, 302)  # Redirect means success
        booking = Booking.objects.filter(passenger=self.passenger_user).last()
        self.assertIsNotNone(booking)
        self.assertEqual(booking.number_of_bags, 1)   # clamped
        self.assertEqual(booking.approx_weight_kg, 20)  # fallback


    def test_13_coolie_action_requires_post(self):
        """Test that GET requests to coolie action endpoints are rejected"""
        booking = Booking.objects.create(
            passenger=self.passenger_user,
            coolie=self.coolie_profile,
            station=self.station,
            platform=self.platform1,
            number_of_bags=1,
            total_fare=Decimal('100.00'),
            status='REQUESTED'
        )
        self.client.login(username="coolie_test", password="cooliepassword")
        resp = self.client.get(reverse('coolies:update_booking_status', args=[booking.booking_id, 'accept']))
        # Should redirect (with error message) not change the booking
        self.assertEqual(resp.status_code, 302)
        booking.refresh_from_db()
        self.assertEqual(booking.status, 'REQUESTED')  # unchanged


    def test_14_logout_requires_post(self):
        """Test that GET logout does not actually log the user out (CSRF protection)"""
        self.client.login(username="passenger_test", password="passpassword")
        # GET logout should redirect but NOT log out
        resp = self.client.get(reverse('accounts:logout'))
        self.assertEqual(resp.status_code, 302)  # redirects
        # User should still be authenticated
        response = self.client.get(reverse('accounts:passenger_dashboard'))
        self.assertEqual(response.status_code, 200)  # still logged in

        # POST logout should actually log out
        resp_post = self.client.post(reverse('accounts:logout'))
        self.assertEqual(resp_post.status_code, 302)
        # Dashboard should redirect to login now
        response2 = self.client.get(reverse('accounts:passenger_dashboard'))
        self.assertEqual(response2.status_code, 302)  # redirect to login
