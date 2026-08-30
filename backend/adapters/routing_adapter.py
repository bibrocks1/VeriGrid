"""
OPTIONAL (Day 10) — flagged cuttable in the Day 10 plan.

Thin wrapper around OSRM's public demo routing server. Uses OSRM
specifically because it needs no API key (unlike Mapbox), which keeps
this deployable for a demo without another credential to manage. The
public demo server is rate-limited and NOT for production use — that's
an explicit tradeoff for hackathon speed, noted here so it isn't
mistaken for a production-ready choice later.
"""
import requests

OSRM_BASE_URL = "https://router.project-osrm.org"


class RoutingAPIError(Exception):
    pass


def _parse_steps(route: dict) -> list[dict]:
    steps = []
    for leg in route.get("legs", []):
        for step in leg.get("steps", []):
            maneuver = step.get("maneuver", {})
            instruction_type = maneuver.get("type", "continue")
            modifier = maneuver.get("modifier")
            road_name = step.get("name") or "the road"
            instruction = instruction_type.replace("_", " ").capitalize()
            if modifier:
                instruction += f" ({modifier})"
            instruction += f" onto {road_name}"
            steps.append(
                {
                    "instruction": instruction,
                    "distanceM": round(step.get("distance", 0), 1),
                    "durationS": round(step.get("duration", 0), 1),
                }
            )
    return steps


def get_route_alternatives(
    origin_lat: float, origin_lon: float,
    dest_lat: float, dest_lon: float,
    max_alternatives: int = 3,
) -> list[dict]:
    """
    Returns a list of route options, each:
        {"geometry": [[lat, lon], ...], "distance_m": float, "duration_s": float,
         "steps": [{"instruction": str, "distanceM": float, "durationS": float}, ...]}
    Ordered as OSRM returns them (first is its default/shortest route).
    """
    url = (
        f"{OSRM_BASE_URL}/route/v1/driving/"
        f"{origin_lon},{origin_lat};{dest_lon},{dest_lat}"
    )
    params = {
        "alternatives": "true",
        "overview": "full",
        "geometries": "geojson",
        "steps": "true",
    }

    try:
        response = requests.get(url, params=params, timeout=15)
    except requests.RequestException as exc:
        raise RoutingAPIError(f"Could not reach routing service: {exc}") from exc

    if not response.ok:
        raise RoutingAPIError(f"Routing service returned {response.status_code}: {response.text}")

    data = response.json()
    if data.get("code") != "Ok":
        raise RoutingAPIError(f"Routing service error: {data.get('message', data.get('code'))}")

    routes = data.get("routes", [])[:max_alternatives]
    if not routes:
        raise RoutingAPIError("No routes found between the given points.")

    results = []
    for route in routes:
        coords = route["geometry"]["coordinates"]  # OSRM returns [lon, lat] pairs
        results.append({
            "geometry": [[lat, lon] for lon, lat in coords],
            "distance_m": route["distance"],
            "duration_s": route["duration"],
            "steps": _parse_steps(route),
        })
    return results
