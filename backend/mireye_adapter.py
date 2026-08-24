import os
import requests
from dotenv import load_dotenv
from adapters.mireye_adapter import get_area_context

load_dotenv()

MIREYE_API_KEY = os.getenv("MIREYE_API_KEY")
MIREYE_BASE_URL = "https://api.mireye.com"

HEADERS = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {MIREYE_API_KEY}"
}


def get_area_context(lat, lon):
    url = f"{MIREYE_BASE_URL}/v1/fetch"

    payload = {
        "lat": lat,
        "lng": lon,
        "fields": [
            "elevation"
        ]
    }

    response = requests.post(
        url,
        headers=HEADERS,
        json=payload,
        timeout=30
    )

    print("MirEye status:", response.status_code)
    print("MirEye response:", response.text)

    response.raise_for_status()

    return response.json()


def push_verified_observation(payload):
    """
    Send a verified VeriGrid observation to the
    appropriate external observation endpoint.

    Endpoint should only be implemented once
    confirmed by the Mireye API documentation/
    subscription access.
    """

    raise NotImplementedError(
        "Mireye observation ingestion endpoint not confirmed yet."
    )