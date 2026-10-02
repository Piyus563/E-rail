"""
RailSaathi WhatsApp Notification Utility — Twilio
Sends booking and status update messages to passenger's WhatsApp.
"""

import logging
from django.conf import settings

logger = logging.getLogger(__name__)


def _get_client():
    """Return Twilio client only if credentials are configured."""
    sid = settings.TWILIO_ACCOUNT_SID
    token = settings.TWILIO_AUTH_TOKEN
    if not sid or not token or sid == 'your_account_sid_here':
        return None
    try:
        from twilio.rest import Client
        return Client(sid, token)
    except Exception as e:
        logger.warning(f"Twilio client init failed: {e}")
        return None


def _format_phone(phone):
    """Normalize phone to E.164 format for WhatsApp."""
    if not phone:
        return None
    # Remove spaces, dashes, brackets
    cleaned = ''.join(c for c in phone if c.isdigit() or c == '+')
    if not cleaned.startswith('+'):
        # Assume India (+91) if no country code
        cleaned = '+91' + cleaned.lstrip('0')
    return f"whatsapp:{cleaned}"


def _site_url():
    """Return the base site URL from settings — avoids hardcoding localhost."""
    return getattr(settings, 'SITE_URL', 'http://127.0.0.1:8000').rstrip('/')


def send_whatsapp(to_phone, message):
    """
    Send a WhatsApp message via Twilio.
    Silently logs and skips if Twilio is not configured.
    """
    client = _get_client()
    if not client:
        logger.info(f"[WhatsApp SKIPPED - Twilio not configured] To: {to_phone} | Msg: {message[:60]}")
        return False

    to_whatsapp = _format_phone(to_phone)
    if not to_whatsapp:
        logger.warning(f"Invalid phone number: {to_phone}")
        return False

    try:
        msg = client.messages.create(
            from_=settings.TWILIO_WHATSAPP_FROM,
            to=to_whatsapp,
            body=message
        )
        logger.info(f"WhatsApp sent: {msg.sid} -> {to_whatsapp}")
        return True
    except Exception as e:
        logger.error(f"WhatsApp send failed to {to_whatsapp}: {e}")
        return False


# --- Booking-specific message helpers ---

def notify_booking_created(booking):
    """Notify passenger when booking is created."""
    phone = booking.passenger.phone
    coolie_name = booking.coolie.user.get_full_name() if booking.coolie else "a nearby Sahayak"
    site = _site_url()
    message = (
        f"🚆 *RailSaathi Booking Confirmed!*\n\n"
        f"Booking ID: *{booking.booking_id}*\n"
        f"Station: {booking.station.name}\n"
        f"Platform: {booking.platform.number if booking.platform else 'TBD'}\n"
        f"Coolie: {coolie_name}\n"
        f"Bags: {booking.number_of_bags} | Fare: ₹{booking.total_fare}\n"
        f"Meeting Point: {booking.meeting_point}\n\n"
        f"Track your booking: {site}/bookings/track/{booking.booking_id}/\n"
        f"_RailSaathi — One Platform for Every Railway Station Need_"
    )
    return send_whatsapp(phone, message)


def notify_booking_accepted(booking):
    """Notify passenger when coolie accepts the booking."""
    phone = booking.passenger.phone
    coolie = booking.coolie
    coolie_name = coolie.user.get_full_name() if coolie else "Sahayak"
    site = _site_url()
    message = (
        f"✅ *Coolie Accepted Your Booking!*\n\n"
        f"Booking ID: *{booking.booking_id}*\n"
        f"Sahayak: *{coolie_name}*\n"
        f"Badge No: {coolie.badge_number if coolie else 'N/A'}\n"
        f"Platform: {booking.platform.number if booking.platform else 'TBD'}\n"
        f"Meeting Point: {booking.meeting_point}\n\n"
        f"Please be at the meeting point on time. 🙏\n"
        f"Track: {site}/bookings/track/{booking.booking_id}/"
    )
    return send_whatsapp(phone, message)


def notify_booking_started(booking):
    """Notify passenger when service starts."""
    phone = booking.passenger.phone
    coolie_name = booking.coolie.user.get_full_name() if booking.coolie else "Sahayak"
    site = _site_url()
    message = (
        f"🧳 *Luggage Service Started!*\n\n"
        f"Booking ID: *{booking.booking_id}*\n"
        f"Sahayak *{coolie_name}* has reached you and started handling your luggage.\n\n"
        f"Track: {site}/bookings/track/{booking.booking_id}/"
    )
    return send_whatsapp(phone, message)


def notify_booking_completed(booking):
    """Notify passenger when service is completed."""
    phone = booking.passenger.phone
    coolie_name = booking.coolie.user.get_full_name() if booking.coolie else "Sahayak"
    site = _site_url()
    message = (
        f"🎉 *Service Completed! Thank You!*\n\n"
        f"Booking ID: *{booking.booking_id}*\n"
        f"Sahayak: {coolie_name}\n"
        f"Total Fare Paid: ₹{booking.total_fare}\n\n"
        f"Please rate your experience ⭐:\n"
        f"{site}/bookings/track/{booking.booking_id}/\n\n"
        f"_Thank you for using RailSaathi!_ 🚆"
    )
    return send_whatsapp(phone, message)


def notify_booking_cancelled(booking):
    """Notify passenger when booking is cancelled."""
    phone = booking.passenger.phone
    site = _site_url()
    message = (
        f"❌ *Booking Cancelled*\n\n"
        f"Booking ID: *{booking.booking_id}*\n"
        f"Your booking has been cancelled.\n"
        f"Reason: {booking.cancellation_reason or 'Cancelled'}\n\n"
        f"Book again: {site}/bookings/book/\n"
        f"_RailSaathi — We're here to help!_"
    )
    return send_whatsapp(phone, message)


def notify_booking_rejected(booking):
    """Notify passenger when coolie rejects the booking."""
    phone = booking.passenger.phone
    site = _site_url()
    message = (
        f"⚠️ *Coolie Unavailable*\n\n"
        f"Booking ID: *{booking.booking_id}*\n"
        f"The assigned Sahayak was unable to accept your request.\n\n"
        f"Please book another available coolie:\n"
        f"{site}/bookings/book/?station={booking.station.code}\n"
        f"_RailSaathi — We'll find you another Sahayak!_"
    )
    return send_whatsapp(phone, message)
