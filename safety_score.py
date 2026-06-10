from location_utils import haversine_distance_meters


def calculate_route_safety_score(route, safety_zones, traveler_type, departure_time):
    """
    Calculates safety score out of 100 using predefined safety zones.
    """
    score = 100
    warnings = []
    nearby_zones = []

    route_coordinates = route["coordinates"]

    for zone in safety_zones:
        zone_near_route = False
        minimum_distance = float("inf")

        for point in route_coordinates:
            distance = haversine_distance_meters(
                point[0],
                point[1],
                zone["latitude"],
                zone["longitude"]
            )

            if distance < minimum_distance:
                minimum_distance = distance

            if distance <= zone["radius_meters"]:
                zone_near_route = True

        if zone_near_route:
            nearby_zones.append(zone)

            if zone["risk_level"] == "High":
                score -= 25
                warnings.append(
                    f"High-risk zone near route: {zone['zone_name']}."
                )
            elif zone["risk_level"] == "Medium":
                score -= 15
                warnings.append(
                    f"Moderate-risk zone near route: {zone['zone_name']}."
                )
            elif zone["risk_level"] == "Low":
                score -= 3

            if zone["crowd_level"] == "High":
                score -= 5
                warnings.append(
                    f"High crowd estimate near: {zone['zone_name']}."
                )

    if traveler_type in ["Women Group", "Family"]:
        for zone in nearby_zones:
            if zone["risk_level"] in ["High", "Medium"]:
                score -= 5
                warnings.append(
                    f"Extra caution recommended for {traveler_type} near {zone['zone_name']}."
                )

    if route["traffic_level"] == "High":
        score -= 5
        warnings.append("Heavy traffic expected on this route.")

    if route["route_difficulty"] == "Moderate":
        score -= 5
    elif route["route_difficulty"] == "Hard":
        score -= 10

    score = max(0, min(100, score))

    if score >= 80:
        safety_label = "Safe"
    elif score >= 60:
        safety_label = "Moderate"
    else:
        safety_label = "Risky"

    return {
        "score": score,
        "safety_label": safety_label,
        "warnings": warnings,
        "nearby_zones": nearby_zones
    }