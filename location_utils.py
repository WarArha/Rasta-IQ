import math


def haversine_distance_meters(lat1, lon1, lat2, lon2):
    """
    Calculates distance between two GPS points in meters.
    """
    earth_radius = 6371000

    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)

    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_lat / 2) ** 2
        + math.cos(lat1_rad)
        * math.cos(lat2_rad)
        * math.sin(delta_lon / 2) ** 2
    )

    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return earth_radius * c


def distance_from_route_meters(current_lat, current_lon, route_coordinates):
    """
    Finds the minimum distance between user's current location
    and the planned route coordinates.
    """
    if not route_coordinates:
        return None

    minimum_distance = float("inf")

    for point in route_coordinates:
        route_lat = point[0]
        route_lon = point[1]

        distance = haversine_distance_meters(
            current_lat,
            current_lon,
            route_lat,
            route_lon
        )

        if distance < minimum_distance:
            minimum_distance = distance

    return minimum_distance


def check_danger_zone(current_lat, current_lon, safety_zones):
    """
    Checks whether current location is inside any predefined danger zone.
    """
    matched_zones = []

    for zone in safety_zones:
        distance = haversine_distance_meters(
            current_lat,
            current_lon,
            zone["latitude"],
            zone["longitude"]
        )

        if distance <= zone["radius_meters"]:
            matched_zones.append({
                "zone": zone,
                "distance_meters": round(distance, 2)
            })

    return matched_zones