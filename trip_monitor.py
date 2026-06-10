import math

# Try to import helper functions from location_utils if compatible
try:
    from location_utils import haversine_distance as imported_haversine
except ImportError:
    imported_haversine = None

def local_haversine_distance(lat1, lon1, lat2, lon2):
    """
    Fallback Haversine formula calculation for distance in meters between two points.
    """
    R = 6371000.0  # Earth radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    
    a = math.sin(delta_phi / 2.0) ** 2 + \
        math.cos(phi1) * math.cos(phi2) * \
        math.sin(delta_lambda / 2.0) ** 2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    
    return R * c

# Choose the available distance function
distance_func = imported_haversine if imported_haversine is not None else local_haversine_distance

def extract_points_from_route(planned_route):
    """
    Helper to extract a list of (lat, lon) tuples from various route formats.
    """
    if not planned_route:
        return []
        
    points = []
    
    # 1. If it's a list of coordinates
    if isinstance(planned_route, list):
        points = planned_route
    # 2. If it's a dictionary
    elif isinstance(planned_route, dict):
        points = (
            planned_route.get("coordinates") or 
            planned_route.get("points") or 
            planned_route.get("path") or 
            planned_route.get("geometry", {}).get("coordinates") or
            []
        )
        # Check if the dictionary itself is a single point
        lat = planned_route.get("lat") or planned_route.get("latitude")
        lon = planned_route.get("lon") or planned_route.get("longitude")
        if lat is not None and lon is not None:
            return [(float(lat), float(lon))]
            
    extracted = []
    for pt in points:
        if isinstance(pt, (list, tuple)) and len(pt) >= 2:
            extracted.append((float(pt[0]), float(pt[1])))
        elif isinstance(pt, dict):
            lat = pt.get("lat") or pt.get("latitude") or pt.get("y")
            lon = pt.get("lon") or pt.get("longitude") or pt.get("x") or pt.get("lng")
            if lat is not None and lon is not None:
                extracted.append((float(lat), float(lon)))
                
    return extracted

def evaluate_trip_location(current_lat, current_lon, planned_route, safety_zones):
    """
    Checks:
    - distance from planned route
    - whether distance is greater than 1000 meters
    - whether current location is inside danger zone

    Returns:
    {
        "distance_from_route_meters": value,
        "is_deviated": True/False,
        "matched_danger_zones": [],
        "alert_level": "Safe" / "Warning" / "Critical",
        "user_message": "...",
        "guardian_alert_needed": True/False,
        "guardian_message": "..."
    }
    """
    # 1. Calculate distance from planned route
    route_points = extract_points_from_route(planned_route)
    
    if not route_points:
        # Default distance is 0 if no route is loaded to prevent false warnings
        distance_from_route_meters = 0.0
    else:
        # Distance to the closest point along the route
        distances = [distance_func(current_lat, current_lon, pt[0], pt[1]) for pt in route_points]
        distance_from_route_meters = min(distances)
        
    # User is deviated if they are more than 1000m from route
    is_deviated = distance_from_route_meters > 1000.0

    # 2. Check if user is inside any danger zone
    matched_danger_zones = []
    if safety_zones and isinstance(safety_zones, list):
        for zone in safety_zones:
            if not isinstance(zone, dict):
                continue
            z_lat = zone.get("lat") or zone.get("latitude")
            z_lon = zone.get("lon") or zone.get("longitude") or zone.get("lng")
            z_rad = zone.get("radius") or zone.get("radius_meters") or zone.get("radius_m", 500)
            z_name = zone.get("name") or zone.get("zone_name", "Unknown Danger Zone")
            z_risk = zone.get("risk_level") or zone.get("level", "Medium")
            
            if z_lat is not None and z_lon is not None:
                dist = distance_func(current_lat, current_lon, float(z_lat), float(z_lon))
                if dist <= float(z_rad):
                    matched_danger_zones.append({
                        "name": z_name,
                        "risk_level": z_risk,
                        "radius_meters": z_rad,
                        "distance_to_center_meters": round(dist, 2)
                    })

    # 3. Determine safety levels
    # Medium/High risk danger zones inside matched_danger_zones
    med_high_zones = [z for z in matched_danger_zones if z["risk_level"].lower() in ["medium", "high", "critical"]]
    has_med_high_zone = len(med_high_zones) > 0
    has_any_zone = len(matched_danger_zones) > 0

    if is_deviated and has_med_high_zone:
        alert_level = "Critical"
    elif not is_deviated and not has_any_zone:
        alert_level = "Safe"
    else:
        # Warning cases:
        # - user is deviated but not in medium/high risk zone (no zone or only low risk zones)
        # - user is inside a risk zone but not deviated
        alert_level = "Warning"

    # Guardian alert is needed only for Critical
    guardian_alert_needed = (alert_level == "Critical")

    # 4. Generate user and guardian messages
    if alert_level == "Safe":
        user_message = "You are on your planned route and in a safe area. Stay safe and enjoy your trip!"
        guardian_message = ""
    elif alert_level == "Warning":
        if is_deviated:
            if has_any_zone:
                zone_names = ", ".join([z["name"] for z in matched_danger_zones])
                user_message = f"Warning: You have deviated {round(distance_from_route_meters)}m from your planned route and are inside safety warning zone: {zone_names}."
            else:
                user_message = f"Warning: You have deviated {round(distance_from_route_meters)}m from your planned route. Please return to the safe path."
        else:
            # User is on route but inside a low/medium/high risk zone (Warning status because not deviated)
            zone_names = ", ".join([z["name"] for z in matched_danger_zones])
            user_message = f"Warning: You are currently passing through a safety warning zone: {zone_names}. Exercise caution."
        guardian_message = ""
    else:  # Critical
        zone_names = ", ".join([z["name"] for z in (med_high_zones if med_high_zones else matched_danger_zones)])
        user_message = (
            f"CRITICAL SAFETY ALERT! You have entered a high-risk danger zone ({zone_names}) "
            f"and are {round(distance_from_route_meters)}m off your planned route. "
            f"An emergency safety alert has been simulated to your guardian."
        )
        guardian_message = (
            f"Emergency Alert! Your contact is off-route and inside a danger zone: '{zone_names}'. "
            f"Current Coordinates: ({current_lat}, {current_lon}). Please contact them immediately."
        )

    return {
        "distance_from_route_meters": round(distance_from_route_meters, 2),
        "is_deviated": is_deviated,
        "matched_danger_zones": matched_danger_zones,
        "alert_level": alert_level,
        "user_message": user_message,
        "guardian_alert_needed": guardian_alert_needed,
        "guardian_message": guardian_message
    }

