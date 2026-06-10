import requests


def get_osrm_road_route(selected_route):
    """
    Gets a road-following route using the free OSRM demo server.

    This uses the first and last coordinates of the selected route.
    If OSRM fails, it safely returns success=False.
    """

    try:
        route_coordinates = selected_route["coordinates"]

        if not route_coordinates or len(route_coordinates) < 2:
            return {
                "success": False,
                "route_source": "sample",
                "coordinates": selected_route["coordinates"],
                "distance_km": selected_route.get("distance_km"),
                "estimated_time": selected_route.get("estimated_time"),
                "error": "Selected route does not have enough coordinates."
            }

        start_lat = route_coordinates[0][0]
        start_lon = route_coordinates[0][1]

        end_lat = route_coordinates[-1][0]
        end_lon = route_coordinates[-1][1]

        osrm_url = (
            "https://router.project-osrm.org/route/v1/driving/"
            f"{start_lon},{start_lat};{end_lon},{end_lat}"
        )

        params = {
            "overview": "full",
            "geometries": "geojson",
            "steps": "false"
        }

        response = requests.get(osrm_url, params=params, timeout=15)

        if response.status_code != 200:
            return {
                "success": False,
                "route_source": "sample",
                "coordinates": selected_route["coordinates"],
                "distance_km": selected_route.get("distance_km"),
                "estimated_time": selected_route.get("estimated_time"),
                "error": f"OSRM request failed with status code {response.status_code}."
            }

        data = response.json()

        if "routes" not in data or len(data["routes"]) == 0:
            return {
                "success": False,
                "route_source": "sample",
                "coordinates": selected_route["coordinates"],
                "distance_km": selected_route.get("distance_km"),
                "estimated_time": selected_route.get("estimated_time"),
                "error": "No road route returned by OSRM."
            }

        osrm_route = data["routes"][0]

        geometry_coordinates = osrm_route["geometry"]["coordinates"]

        road_coordinates = []

        for point in geometry_coordinates:
            lon = point[0]
            lat = point[1]
            road_coordinates.append([lat, lon])

        distance_km = round(osrm_route["distance"] / 1000, 2)
        duration_minutes = round(osrm_route["duration"] / 60)

        return {
            "success": True,
            "route_source": "OSRM Road Route",
            "coordinates": road_coordinates,
            "distance_km": distance_km,
            "estimated_time": f"{duration_minutes} minutes",
            "error": None
        }

    except Exception as error:
        return {
            "success": False,
            "route_source": "sample",
            "coordinates": selected_route.get("coordinates", []),
            "distance_km": selected_route.get("distance_km"),
            "estimated_time": selected_route.get("estimated_time"),
            "error": str(error)
        }