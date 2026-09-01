import os
from typing import Any

import requests
from dotenv import load_dotenv


load_dotenv()

MIREYE_API_KEY = os.getenv("MIREYE_API_KEY")
MIREYE_BASE_URL = os.getenv(
    "MIREYE_BASE_URL",
    "https://api.mireye.com/v1"
)


class MireyeAPIError(Exception):
    """Raised when a Mireye API request fails."""
    pass


def get_area_context(
    lat: float,
    lon: float,
) -> dict[str, Any]:

    Args:
        lat: Latitude.
        lon: Longitude.
        preset: Mireye data preset to request — the live API supports 14
            (terrain, flood_risk, natural_hazard, utilities, ...), each
            returning a different field set. A previous version of this
            adapter dropped this parameter entirely and always fetched one
            fixed field list, which broke category-specific credibility
            checks (mireye_service.py) that need e.g. flood_risk for
            flooding reports and natural_hazard for safety reports.

    if not api_key:
        raise RuntimeError(
            "MIREYE_API_KEY is not set in backend/.env"
        )

    if not -90 <= lat <= 90:
        raise ValueError(f"Invalid latitude: {lat}")

    if not -180 <= lon <= 180:
        raise ValueError(f"Invalid longitude: {lon}")

    url = "https://api.mireye.com/v1/fetch"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "lat": lat,
        "lng": lon,
        "fields": [
            "elevation",
            "slope_degrees",
            "aspect_cardinal",
            "coast_distance_m",
            "bedrock_depth_cm",
            "soil_drainage_class",
        ],
    }

    try:
        response = requests.post(
            url,
            headers=headers,
            json=payload,
            timeout=30,
        )

    except requests.RequestException as exc:
        raise MireyeAPIError(
            f"Could not connect to Mireye: {exc}"
        ) from exc

    if not response.ok:
        raise MireyeAPIError(
            f"Mireye API returned {response.status_code}: "
            f"{response.text}"
        )

    try:
        return response.json()

    except ValueError as exc:
        raise MireyeAPIError(
            "Mireye returned a non-JSON response."
        ) from exc
    
def push_verified_observation(
    payload: dict[str, Any],
) -> dict[str, Any]:
    """
    Push a verified VeriGrid observation to Mireye.

    NOTE:
    The currently documented Mireye Earth API does not expose
    a public observation-write endpoint. Keep this function as
    an adapter boundary until your Mireye subscription provides
    the appropriate write endpoint.
    """

    raise NotImplementedError(
        "Mireye observation push endpoint has not been provided. "
        "Do not invent an endpoint; configure this once the "
        "Mireye write API is available."
    )
