import os
import json
from dotenv import load_dotenv

load_dotenv()

try:
    import google.generativeai as genai
    HAS_GENAI = True
except ImportError:
    HAS_GENAI = False


def generate_trip_plan(trip_request, selected_route, safety_result):
    """
    Takes:
    - trip_request dictionary
    - selected_route dictionary
    - safety_result dictionary

    Returns:
    {
        "success": True/False,
        "mode": "gemini" or "fallback",
        "itinerary": "...",
        "budget_breakdown": "...",
        "safety_notes": "...",
        "error": None or "..."
    }
    """

    src = trip_request.get("source") or trip_request.get("source_city") or "Islamabad"
    dest = trip_request.get("destination") or trip_request.get("destination_city") or "Murree"

    try:
        budget = int(trip_request.get("budget", 10000))
    except (ValueError, TypeError):
        budget = 10000

    try:
        days = int(trip_request.get("days", 3))
    except (ValueError, TypeError):
        days = 3

    traveler_type = trip_request.get("traveler_type", "Solo")
    preferences = trip_request.get("preferences", [])

    if isinstance(preferences, list):
        preferences_text = ", ".join(preferences) if preferences else "nature and sightseeing"
    else:
        preferences_text = str(preferences) if preferences else "nature and sightseeing"

    guardian_name = trip_request.get("guardian_name", "Guardian")
    guardian_phone = trip_request.get("guardian_phone", "03XXXXXXXXX")

    route_name = selected_route.get("route_name", f"{src} to {dest} Main Route")
    distance = selected_route.get("distance_km") or selected_route.get("total_distance") or "N/A"
    duration = selected_route.get("estimated_time") or selected_route.get("average_duration") or "N/A"

    safety_score = safety_result.get("score") or safety_result.get("safety_score") or 100
    safety_label = safety_result.get("safety_label", "Safe")

    warnings = safety_result.get("warnings", []) or safety_result.get("safety_warnings", [])
    if isinstance(warnings, str):
        warnings = [warnings]

    fallback_itinerary_lines = []

    for d in range(1, days + 1):
        fallback_itinerary_lines.append(f"### Day {d}")

        if d == 1:
            fallback_itinerary_lines.append(
                f"- **Morning**: Depart from {src} towards {dest} via {route_name} "
                f"(Distance: {distance} km, Estimated Time: {duration})."
            )
            fallback_itinerary_lines.append(
                f"- **Afternoon**: Check in at a safe hotel/guesthouse in {dest}. Rest and review the route safety notes."
            )
            fallback_itinerary_lines.append(
                "- **Evening**: Visit nearby public areas or main markets. Avoid isolated places after dark."
            )

        elif d == days:
            fallback_itinerary_lines.append(
                f"- **Morning**: Visit final nearby attractions in {dest} based on your preferences: {preferences_text}."
            )
            fallback_itinerary_lines.append(
                "- **Afternoon**: Pack bags, check out, and begin return preparation."
            )
            fallback_itinerary_lines.append(
                f"- **Evening**: Travel back toward {src} safely and keep guardian/family updated."
            )

        else:
            fallback_itinerary_lines.append(
                f"- **Morning**: Explore tourist places in {dest} matching your preferences: {preferences_text}."
            )
            fallback_itinerary_lines.append(
                "- **Afternoon**: Continue sightseeing in public and family-friendly areas."
            )
            fallback_itinerary_lines.append(
                "- **Evening**: Return to your stay before late night. Avoid low-crowd isolated routes."
            )

        fallback_itinerary_lines.append("")

    fallback_itinerary = "\n".join(fallback_itinerary_lines)

    fallback_budget_breakdown = (
        f"Total Budget Allocated: {budget:,} PKR\n\n"
        f"- **Accommodation**: {int(budget * 0.40):,} PKR\n"
        f"- **Transport & Fuel**: {int(budget * 0.25):,} PKR\n"
        f"- **Food & Snacks**: {int(budget * 0.20):,} PKR\n"
        f"- **Sightseeing/Entry**: {int(budget * 0.10):,} PKR\n"
        f"- **Emergency Reserve**: {int(budget * 0.05):,} PKR"
    )

    warning_bullets = (
        "\n".join([f"- ⚠️ {w}" for w in warnings])
        if warnings
        else "- No major predefined safety risks detected for the selected route."
    )

    fallback_safety_notes = (
        f"**Safety Score**: {safety_score}/100 — {safety_label}\n\n"
        f"**Active Warnings for Route:**\n{warning_bullets}\n\n"
        f"**Safety Recommendation for {traveler_type} Travelers:**\n"
        "- Prefer daylight travel, especially for mountain or low-crowd areas.\n"
        "- Keep offline maps downloaded and maintain phone battery.\n"
        "- Avoid isolated roads and low-crowd areas after dark.\n"
        "- Keep guardian/family updated during the trip.\n"
        f"- Registered guardian: {guardian_name} ({guardian_phone})."
    )

    api_key = os.environ.get("GEMINI_API_KEY")

    if not HAS_GENAI:
        return {
            "success": True,
            "mode": "fallback",
            "itinerary": fallback_itinerary,
            "budget_breakdown": fallback_budget_breakdown,
            "safety_notes": fallback_safety_notes,
            "error": "google-generativeai package not installed. Using fallback itinerary."
        }

    if not api_key:
        return {
            "success": True,
            "mode": "fallback",
            "itinerary": fallback_itinerary,
            "budget_breakdown": fallback_budget_breakdown,
            "safety_notes": fallback_safety_notes,
            "error": "GEMINI_API_KEY environment variable is not set. Using fallback itinerary."
        }

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-1.5-flash")

        prompt = (
            f"You are the Rasta IQ AI Travel & Safety Companion for Pakistan. "
            f"Generate a customized, budget-friendly and safety-aware trip plan.\n\n"
            f"Source: {src}\n"
            f"Destination: {dest}\n"
            f"Budget: {budget} PKR\n"
            f"Days: {days}\n"
            f"Traveler Type: {traveler_type}\n"
            f"Preferences: {preferences_text}\n"
            f"Selected Route: {route_name}\n"
            f"Distance: {distance} km\n"
            f"Estimated Time: {duration}\n"
            f"Route Safety Score: {safety_score}/100 — {safety_label}\n"
            f"Route Warnings: {', '.join(warnings) if warnings else 'None'}\n\n"
            f"Important limitations:\n"
            f"- Do not claim real-time harassment prediction.\n"
            f"- Mention that safety is based on predefined safety zones and route analysis.\n\n"
            f"Respond with a raw JSON object containing exactly these string keys: "
            f"'itinerary', 'budget_breakdown', and 'safety_notes'. "
            f"Do not use markdown code fences."
        )

        response = model.generate_content(prompt)
        response_text = response.text.strip()

        if response_text.startswith("```"):
            lines = response_text.splitlines()
            if lines[0].startswith("```json") or lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            response_text = "\n".join(lines).strip()

        data = json.loads(response_text)

        return {
            "success": True,
            "mode": "gemini",
            "itinerary": data.get("itinerary", fallback_itinerary),
            "budget_breakdown": data.get("budget_breakdown", fallback_budget_breakdown),
            "safety_notes": data.get("safety_notes", fallback_safety_notes),
            "error": None
        }

    except Exception as e:
        return {
            "success": True,
            "mode": "fallback",
            "itinerary": fallback_itinerary,
            "budget_breakdown": fallback_budget_breakdown,
            "safety_notes": fallback_safety_notes,
            "error": f"Gemini API failure: {str(e)}. Using fallback itinerary."
        }