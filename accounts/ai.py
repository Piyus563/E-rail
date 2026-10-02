"""Explainable AI helpers for RailSaathi's station assistant."""

from django.db.models import Q

from .models import CoolieProfile


INTENT_RESPONSES = {
    'map': "Open the station map to see platforms, lifts, washrooms, food, and help desks around NJP.",
    'lost': "Use Lost & Found to register a report with the item's location and your contact number. Keep the report ID for tracking.",
    'complaint': "You can lodge a complaint about cleanliness, facilities, safety, or coolie service and track its ticket from your dashboard.",
    'assistance': "RailSaathi can arrange wheelchair, senior citizen, medical, and general passenger assistance at your platform.",
    'fare': "Coolie fare starts at Rs. 100 for one bag, plus Rs. 50 for each additional bag. The booking form shows the live total.",
}


def recommend_coolies(station_code='NJP', number_of_bags=1, needs_assistance=False):
    """Rank verified online coolies using transparent service signals."""
    coolies = CoolieProfile.objects.filter(
        station__code__iexact=station_code,
        is_verified=True,
        is_online=True,
    ).select_related('user', 'station', 'current_platform')

    ranked = []
    for coolie in coolies:
        score = float(coolie.rating) * 20
        score += min(coolie.experience_years, 10) * 2
        if coolie.current_platform:
            score += 5
        if number_of_bags >= 4 and coolie.experience_years >= 5:
            score += 8
        if needs_assistance and coolie.current_platform and coolie.current_platform.has_wheelchair_ramp:
            score += 10
        ranked.append((score, coolie))

    ranked.sort(key=lambda item: (-item[0], -float(item[1].rating), item[1].id))

    # Use the score captured per-item, not the loop variable (closure fix)
    return [
        {
            'id': coolie.id,
            'name': coolie.user.get_full_name() or coolie.user.username,
            'badge_number': coolie.badge_number,
            'rating': float(coolie.rating),
            'experience_years': coolie.experience_years,
            'current_platform': coolie.current_platform.number if coolie.current_platform else None,
            'score': round(item_score, 1),
            'reason': _recommendation_reason(coolie, number_of_bags, needs_assistance),
        }
        for item_score, coolie in ranked[:5]
    ]


def _recommendation_reason(coolie, number_of_bags, needs_assistance):
    reasons = [f"Rated {coolie.rating}/5"]
    if coolie.experience_years >= 5:
        reasons.append(f"{coolie.experience_years} years' experience")
    if number_of_bags >= 4 and coolie.experience_years >= 5:
        reasons.append("experienced with heavier luggage")
    if needs_assistance and coolie.current_platform and coolie.current_platform.has_wheelchair_ramp:
        reasons.append("near a wheelchair-accessible platform")
    return ', '.join(reasons)


def assistant_reply(message):
    """Return a safe, useful response for common station-help intents."""
    normalized = message.lower()
    for keywords, response in [
        (('map', 'platform', 'direction', 'where'), INTENT_RESPONSES['map']),
        (('lost', 'missing', 'found'), INTENT_RESPONSES['lost']),
        (('complaint', 'grievance', 'overcharg'), INTENT_RESPONSES['complaint']),
        (('wheelchair', 'senior', 'medical', 'assistance', 'help'), INTENT_RESPONSES['assistance']),
        (('fare', 'price', 'cost', 'charge'), INTENT_RESPONSES['fare']),
    ]:
        if any(keyword in normalized for keyword in keywords):
            return response
    return "I can help with coolie bookings, station maps, passenger assistance, facilities, lost items, fares, and complaints. What do you need at the station?"
