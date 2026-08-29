import os
import requests
from dotenv import load_dotenv

load_dotenv()

MIREYE_API_KEY = os.getenv("MIREYE_API_KEY")
MIREYE_BASE_URL = os.getenv(
    "MIREYE_BASE_URL",
    "https://api.mireye.com"
)

HEADERS = {
    "Authorization": f"Bearer {MIREYE_API_KEY}",
    "Content-Type": "application/json",
}


def get_area_context(lat: float, lon: float):
    url = f"{MIREYE_BASE_URL}/v1/fetch"

    payload = {
        "lat": lat,
        "lng": lon,
        "preset": "terrain"
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
    raise NotImplementedError(
        "Mireye observation ingestion endpoint not confirmed yet."
    )