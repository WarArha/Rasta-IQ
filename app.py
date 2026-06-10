
import json
from pathlib import Path
import folium

import streamlit as st
from streamlit_folium import st_folium  
from safety_score import calculate_route_safety_score
from road_route_service import get_osrm_road_route
from gemini_service import generate_trip_plan

from trip_monitor import evaluate_trip_location
from sms_service import send_guardian_alert

st.set_page_config(
    page_title="Rasta IQ",
    page_icon="🛡️",
    layout="wide"
)
if "trip_result" not in st.session_state:
    st.session_state.trip_result = None

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"


def load_json_file(file_name):
    file_path = DATA_DIR / file_name

    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)


def find_matching_route(routes, source, destination):
    source_lower = source.strip().lower()
    destination_lower = destination.strip().lower()

    for route in routes:
        route_source = route["source"].strip().lower()
        route_destination = route["destination"].strip().lower()

        if route_source == source_lower and route_destination == destination_lower:
            return route

    # fallback route for demo
    return routes[0]





def get_zone_color(risk_level):
    """
    Returns map color based on zone risk level.
    """
    if risk_level == "High":
        return "red"
    if risk_level == "Medium":
        return "orange"
    return "green"


def create_route_safety_map(route, safety_zones):
    """
    Creates a Folium map showing:
    - planned route
    - route points
    - predefined safety/risk zones
    """

    route_coordinates = route["coordinates"]

    if not route_coordinates:
        return None

    # Start map from first route coordinate
    start_lat = route_coordinates[0][0]
    start_lon = route_coordinates[0][1]

    route_map = folium.Map(
        location=[start_lat, start_lon],
        zoom_start=10
    )

    # Draw planned route line
    folium.PolyLine(
        locations=route_coordinates,
        color="blue",
        weight=5,
        opacity=0.8,
        tooltip="Planned Safe Route"
    ).add_to(route_map)

    # Source marker
    folium.Marker(
        location=route_coordinates[0],
        popup=f"Source: {route['source']}",
        tooltip="Source",
        icon=folium.Icon(color="blue", icon="play")
    ).add_to(route_map)

    # Destination marker
    folium.Marker(
        location=route_coordinates[-1],
        popup=f"Destination: {route['destination']}",
        tooltip="Destination",
        icon=folium.Icon(color="green", icon="flag")
    ).add_to(route_map)

    # Route point markers
# Route point markers
# For road-following routes, there can be many points, so we only show some markers.
    marker_gap = max(1, len(route_coordinates) // 10)

    for index, point in enumerate(route_coordinates):
        if index % marker_gap == 0 or index == len(route_coordinates) - 1:
            folium.CircleMarker(
                location=point,
                radius=4,
                color="blue",
                fill=True,
                fill_opacity=0.7,
                popup=f"Route Point {index + 1}"
            ).add_to(route_map)

    # Safety zone circles
    for zone in safety_zones:
        zone_color = get_zone_color(zone["risk_level"])

        popup_text = (
            f"<b>{zone['zone_name']}</b><br>"
            f"City: {zone['city']}<br>"
            f"Risk Level: {zone['risk_level']}<br>"
            f"Crowd Level: {zone['crowd_level']}<br>"
            f"Reason: {zone['risk_reason']}<br>"
            f"Avoid After: {zone['avoid_after']}<br>"
            f"Action: {zone['recommended_action']}"
        )

        folium.Circle(
            location=[zone["latitude"], zone["longitude"]],
            radius=zone["radius_meters"],
            color=zone_color,
            fill=True,
            fill_color=zone_color,
            fill_opacity=0.2,
            popup=popup_text,
            tooltip=f"{zone['risk_level']} Risk Zone"
        ).add_to(route_map)

        folium.Marker(
            location=[zone["latitude"], zone["longitude"]],
            popup=popup_text,
            tooltip=zone["zone_name"],
            icon=folium.Icon(color=zone_color, icon="info-sign")
        ).add_to(route_map)

    return route_map
# -------------------------------
# Page Header
# -------------------------------
st.title("🛡️ Rasta IQ")
st.subheader("AI Safety & Tourism Companion for Pakistan")

st.write(
    "Plan safer journeys across Pakistan using AI trip planning, "
    "predefined safety zones, route safety scoring, and guardian alerts."
)

st.divider()

# -------------------------------
# Trip Input Form
# -------------------------------
st.header("Plan Your Safe Trip")

with st.form("trip_input_form", enter_to_submit=False):
    col1, col2 = st.columns(2)

    with col1:
        source = st.text_input(
            "Starting Location",
            placeholder="Example: Islamabad"
        )

        destination = st.text_input(
            "Destination",
            placeholder="Example: Murree"
        )

        budget = st.number_input(
            "Budget (PKR)",
            min_value=0,
            step=1000,
            value=25000
        )

    with col2:
        days = st.number_input(
            "Number of Days",
            min_value=1,
            max_value=15,
            value=3
        )

        travel_date = st.date_input("Travel Date")

        departure_time = st.time_input("Preferred Departure Time")

    st.subheader("Traveler Type")

    traveler_type = st.radio(
        "Select traveler type",
        ["Solo", "Family", "Women Group", "Students", "Friends"],
        horizontal=True
    )

    st.subheader("Travel Preferences")

    preferences = st.multiselect(
        "Select your preferences",
        [
            "Nature",
            "Historical Places",
            "Food",
            "Adventure",
            "Shopping",
            "Hidden Gems",
            "Family Friendly",
            "Low Budget",
            "Safer Routes"
        ]
    )
    st.subheader("Route Map Option")

    use_road_route = st.checkbox(
        "Use road-following route instead of demo straight route",
        help="This tries to draw the route through actual roads using a free OSRM demo routing service. If it fails, the app will use the current demo route."
    )

    st.subheader("Guardian Safety Mode")

    guardian_mode = st.checkbox("Enable Guardian Safety Alerts")

    guardian_name = ""
    guardian_phone = ""

    
    if guardian_mode:
        guardian_name = st.text_input(
            "Guardian Name",
            placeholder="Example: Ahmed Khan"
        )

        guardian_phone = st.text_input(
            "Guardian Phone Number",
            placeholder="Example: 03001234567"
        )

        st.info(
            "Guardian alerts will only be used for safety warnings during trip monitoring."
        )

    st.warning(
        "Rasta IQ does not predict harassment in real time. "
        "It uses predefined safety zones, estimated crowd/safety levels, "
        "time-based rules, and route analysis to recommend safer travel decisions."
    )

    submitted = st.form_submit_button(
    "Generate Safe Trip Plan",
    type="primary",
    use_container_width=True
)

# -------------------------------
# Form Validation and Output
# -------------------------------
if submitted:
    errors = []

    if not source.strip():
        errors.append("Starting location is required.")

    if not destination.strip():
        errors.append("Destination is required.")

    if budget <= 0:
        errors.append("Budget must be greater than 0.")

    if guardian_mode:
        if not guardian_name.strip():
            errors.append("Guardian name is required when guardian mode is enabled.")

        if not guardian_phone.strip():
            errors.append("Guardian phone number is required when guardian mode is enabled.")
        elif len(guardian_phone.strip()) < 10:
            errors.append("Guardian phone number seems too short.")

    if errors:
        for error in errors:
            st.error(error)
    else:
        trip_request = {
            "source": source,
            "destination": destination,
            "budget": budget,
            "days": days,
            "travel_date": str(travel_date),
            "departure_time": str(departure_time),
            "traveler_type": traveler_type,
            "preferences": preferences,
            "guardian_mode": guardian_mode,
            "guardian_name": guardian_name,
            "guardian_phone": guardian_phone,
            "use_road_route": use_road_route
        }

        

        safety_zones = load_json_file("safety_zones.json")
        sample_routes = load_json_file("sample_routes.json")
        tourist_places = load_json_file("tourist_places.json")
        selected_route = find_matching_route(
            sample_routes,
            source,
            destination
        )

        safety_result = calculate_route_safety_score(
            selected_route,
            safety_zones,
            traveler_type,
            str(departure_time)
        )
        road_route_result = None

        if use_road_route:
            road_route_result = get_osrm_road_route(selected_route)

        trip_plan_result = generate_trip_plan(
        trip_request,
        selected_route,
        safety_result
    )
        st.session_state.trip_result = {
        "trip_request": trip_request,
        "selected_route": selected_route,
        "safety_result": safety_result,
        "safety_zones": safety_zones,
        "road_route_result": road_route_result,
        "trip_plan_result": trip_plan_result,
        "tourist_places": tourist_places
    }
        # -------------------------------
# Display Saved Trip Result
# -------------------------------
if st.session_state.trip_result is not None:
    trip_request = st.session_state.trip_result["trip_request"]
    selected_route = st.session_state.trip_result["selected_route"]
    safety_result = st.session_state.trip_result["safety_result"]
    safety_zones = st.session_state.trip_result["safety_zones"]
    road_route_result = st.session_state.trip_result.get("road_route_result")
    trip_plan_result = st.session_state.trip_result.get("trip_plan_result")
    tourist_places = st.session_state.trip_result.get("tourist_places", [])

    st.success("Trip details saved. Generating safety analysis...")

    st.subheader("Trip Request Data")
    st.json(trip_request)

    st.divider()

    st.header("Recommended Route")

    st.write(f"**Route Name:** {selected_route['route_name']}")
    if road_route_result and road_route_result["success"]:
        st.success("Map Route Source: Road-following route generated successfully.")
    elif trip_request.get("use_road_route"):
        st.warning("Map Route Source: Road route failed, so demo/sample route is being used.")
    else:
        st.info("Map Route Source: Demo/sample route coordinates.")



    display_distance = selected_route["distance_km"]
    display_time = selected_route["estimated_time"]

    if road_route_result and road_route_result["success"]:
        display_distance = road_route_result["distance_km"]
        display_time = road_route_result["estimated_time"]


    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Distance", f"{display_distance} km")

    with col2:
        st.metric("Estimated Time", display_time)

    with col3:
        st.metric("Traffic Level", selected_route["traffic_level"])

    st.write(f"**Route Difficulty:** {selected_route['route_difficulty']}")

    st.divider()

    st.header("Route Safety Score")

    score = safety_result["score"]
    safety_label = safety_result["safety_label"]

    if safety_label == "Safe":
        st.success(f"Safety Score: {score}/100 — {safety_label}")
    elif safety_label == "Moderate":
        st.warning(f"Safety Score: {score}/100 — {safety_label}")
    else:
        st.error(f"Safety Score: {score}/100 — {safety_label}")
    st.caption(
        "This score is calculated using predefined safety zones, estimated crowd level, "
        "route difficulty, traffic level, and traveler type."
    )
    if safety_result["warnings"]:
        st.subheader("Safety Warnings")
        for warning in safety_result["warnings"]:
            st.warning(warning)
    else:
        st.success("No major safety risks detected on this route.")

    if safety_result["nearby_zones"]:
        st.subheader("Nearby Safety/Risk Zones")

        for zone in safety_result["nearby_zones"]:
            with st.expander(zone["zone_name"]):
                st.write(f"**City:** {zone['city']}")
                st.write(f"**Risk Level:** {zone['risk_level']}")
                st.write(f"**Crowd Level:** {zone['crowd_level']}")
                st.write(f"**Reason:** {zone['risk_reason']}")
                st.write(f"**Avoid After:** {zone['avoid_after']}")
                st.write(f"**Recommended Action:** {zone['recommended_action']}")
    st.divider()

    st.header("AI / Fallback Trip Itinerary")

    if trip_plan_result:
        if trip_plan_result["mode"] == "gemini":
            st.success("Gemini AI itinerary generated successfully.")
        else:
            st.info("Fallback itinerary shown because Gemini API key/package is missing or Gemini is unavailable.")

        if trip_plan_result.get("error"):
            with st.expander("AI Itinerary Status"):
                st.write(trip_plan_result["error"])

        st.subheader("Day-wise Itinerary")
        st.markdown(trip_plan_result["itinerary"])

        st.subheader("Budget Breakdown")
        st.markdown(trip_plan_result["budget_breakdown"])

        st.subheader("Safety Notes")
        st.markdown(trip_plan_result["safety_notes"])
    else:
        st.warning("Trip itinerary could not be generated.")


    st.divider()
    

    st.header("Recommended Tourist Places")

    destination_city = trip_request["destination"].strip().lower()

    matching_places = []

    for place in tourist_places:
        place_city = place.get("city", "").strip().lower()

        if place_city == destination_city:
            matching_places.append(place)

    if matching_places:
        st.write(
            f"Here are some suggested tourist places for **{trip_request['destination']}** "
            "based on the available MVP destination data."
        )

        cols = st.columns(3)

        for index, place in enumerate(matching_places):
            with cols[index % 3]:
                with st.container(border=True):
                    st.subheader(place.get("place_name", "Unknown Place"))

                    st.write(f"**Category:** {place.get('category', 'N/A')}")
                    st.write(f"**Estimated Cost:** PKR {place.get('estimated_cost', 'N/A')}")
                    st.write(f"**Recommended Time:** {place.get('recommended_time', 'N/A')}")

                    family_friendly = "Yes" if place.get("family_friendly") else "No"
                    st.write(f"**Family Friendly:** {family_friendly}")

                    st.info(place.get("safety_note", "No safety note available."))

    else:
        st.info(
            f"No tourist places are currently available for **{trip_request['destination']}** "
            "in the MVP data. More destinations can be added in future updates."
        )
    st.divider()
    st.header("Route Safety Map")

    st.caption(
        "Blue line shows the planned route. "
        "Red, orange, and green circles represent predefined high, medium, and low safety zones."
    )
    st.markdown(
        """
        **Map Legend**
        - 🔵 Blue line: Planned safe route
        - 🔴 Red circle: High-risk zone
        - 🟠 Orange circle: Medium-risk zone
        - 🟢 Green circle: Low-risk/safe zone
        """
    )
    map_route = selected_route.copy()

    if road_route_result and road_route_result["success"]:
        map_route["coordinates"] = road_route_result["coordinates"]
        map_route["distance_km"] = road_route_result["distance_km"]
        map_route["estimated_time"] = road_route_result["estimated_time"]

    route_map = create_route_safety_map(map_route, safety_zones)

    if route_map is not None:
        st_folium(route_map, width=1100, height=500)
    else:
        st.error("Map could not be generated because route coordinates are missing.")
        



    st.divider()

    st.header("Active Trip Monitoring Simulation")

    st.caption(
        "This section simulates how Rasta IQ can check whether a traveler is on the planned route "
        "or has moved into a predefined safety/risk zone. This is an MVP simulation, not background GPS tracking."
    )

    start_monitoring = st.checkbox("Start Trip Monitoring Simulation")

    if start_monitoring:
        st.subheader("Select Simulated Current Location")

        location_preset = st.radio(
            "Choose a demo scenario",
            [
                "On Safe Route",
                "Slightly Away From Route",
                "Inside Risk Zone / Warning Demo",
                "Inside Risk Zone / Critical Demo",
                "Custom Coordinates"
            ]
        )

        if location_preset == "On Safe Route":
            current_lat = selected_route["coordinates"][0][0]
            current_lon = selected_route["coordinates"][0][1]

        elif location_preset == "Slightly Away From Route":
            current_lat = selected_route["coordinates"][0][0] + 0.02
            current_lon = selected_route["coordinates"][0][1] + 0.02

        elif location_preset == "Inside Risk Zone / Warning Demo":
            if safety_zones:
                current_lat = safety_zones[0]["latitude"]
                current_lon = safety_zones[0]["longitude"]
            else:
                current_lat = selected_route["coordinates"][0][0]
                current_lon = selected_route["coordinates"][0][1]

        elif location_preset == "Inside Risk Zone / Critical Demo":
            high_or_medium_zone = None

            for zone in safety_zones:
                if zone["risk_level"] in ["High", "Medium"]:
                    high_or_medium_zone = zone
                    break

            if high_or_medium_zone:
                current_lat = high_or_medium_zone["latitude"]
                current_lon = high_or_medium_zone["longitude"]
            else:
                current_lat = selected_route["coordinates"][-1][0]
                current_lon = selected_route["coordinates"][-1][1]

        else:
            col_lat, col_lon = st.columns(2)

            with col_lat:
                current_lat = st.number_input(
                    "Current Latitude",
                    value=float(selected_route["coordinates"][0][0]),
                    format="%.6f"
                )

            with col_lon:
                current_lon = st.number_input(
                    "Current Longitude",
                    value=float(selected_route["coordinates"][0][1]),
                    format="%.6f"
                )

        monitoring_route = selected_route.copy()

        if road_route_result and road_route_result.get("success"):
            monitoring_route["coordinates"] = road_route_result["coordinates"]

        monitoring_result = evaluate_trip_location(
            current_lat,
            current_lon,
            monitoring_route,
            safety_zones
        )

        st.write(f"**Current Simulated Location:** `{current_lat}, {current_lon}`")

        alert_level = monitoring_result["alert_level"]

        if alert_level == "Safe":
            st.success(f"Status: {alert_level}")
        elif alert_level == "Warning":
            st.warning(f"Status: {alert_level}")
        else:
            st.error(f"Status: {alert_level}")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                "Distance From Route",
                f"{monitoring_result['distance_from_route_meters']} m"
            )

        with col2:
            st.metric(
                "Route Deviation",
                "Yes" if monitoring_result["is_deviated"] else "No"
            )

        with col3:
            st.metric(
                "Guardian Alert Needed",
                "Yes" if monitoring_result["guardian_alert_needed"] else "No"
            )

        st.subheader("User Safety Message")
        st.write(monitoring_result["user_message"])

        if monitoring_result["matched_danger_zones"]:
            st.subheader("Matched Safety/Risk Zones")

            for zone in monitoring_result["matched_danger_zones"]:
                with st.expander(zone["name"]):
                    st.write(f"**Risk Level:** {zone['risk_level']}")
                    st.write(f"**Radius:** {zone['radius_meters']} meters")
                    st.write(
                        f"**Distance to Zone Center:** "
                        f"{zone['distance_to_center_meters']} meters"
                    )
        else:
            st.success("No safety/risk zone matched for the current simulated location.")



















        if monitoring_result["guardian_alert_needed"]:
            st.error("Guardian alert condition reached. Simulated SMS alert generated.")

            sms_result = send_guardian_alert(
                guardian_phone=trip_request.get("guardian_phone", ""),
                guardian_name=trip_request.get("guardian_name", ""),
                alert_message=monitoring_result["guardian_message"],
                simulate=True
            )

            st.subheader("Guardian SMS Alert Simulation")

            if sms_result["sent"]:
                st.success("SMS alert simulated successfully.")
            else:
                st.warning("SMS alert could not be simulated.")

            col1, col2 = st.columns(2)

            with col1:
                st.write(f"**Mode:** {sms_result['mode']}")
                st.write(f"**Sent:** {sms_result['sent']}")

            with col2:
                st.write(f"**Guardian Name:** {trip_request.get('guardian_name', 'Not provided')}")
                st.write(f"**Guardian Phone:** {trip_request.get('guardian_phone', 'Not provided')}")

            if sms_result["message"]:
                st.text_area(
                    "SMS Preview",
                    value=sms_result["message"],
                    height=150,
                    disabled=True
                )

            if sms_result["error"]:
                st.error(sms_result["error"])

        else:
            st.info("No guardian alert required for this scenario.")






























    st.divider()

    with st.expander("MVP Limitations and Future Scope"):
        st.markdown(
            """
            **Current MVP Limitations**

            - Rasta IQ uses predefined safety/risk zones stored in local JSON data.
            - The app does not predict harassment in real time.
            - Crowd and safety levels are estimated, not live-detected.
            - Trip monitoring is simulated for MVP demonstration.
            - Guardian SMS alerts are simulated and not sent through a real telecom network.
            - Road-following route uses a free routing service and falls back to demo coordinates if unavailable.
            - Monitoring works only while the Streamlit web app is open and active.

            **Future Scope**

            - Add real mobile GPS tracking using a mobile app.
            - Add Firebase for live guardian updates.
            - Add Google Routes API for production-grade traffic-aware routing.
            - Add verified safety-zone data from trusted public/community sources.
            - Add real SMS or WhatsApp alert integration.
            - Add nearby emergency services such as hospitals and police stations.
            - Add Urdu and Roman Urdu support.
            """
        )







    st.divider()

    if st.button("Clear Trip Plan"):
        st.session_state.trip_result = None
        st.rerun()