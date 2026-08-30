import requests


NOAA_BASE_URL = "https://api.weather.gov"


class NOAAAPIError(RuntimeError):
    pass


def _validate_coordinates(lat: float, lon: float):
    if not -90 <= lat <= 90:
        raise ValueError("Latitude must be between -90 and 90")

    if not -180 <= lon <= 180:
        raise ValueError("Longitude must be between -180 and 180")


def get_weather_context(lat: float, lon: float):
    _validate_coordinates(lat, lon)

    headers = {
        "User-Agent": "VeriGrid/1.0 civic-hazard-research"
    }

    try:
        points_response = requests.get(
            f"{NOAA_BASE_URL}/points/{lat},{lon}",
            headers=headers,
            timeout=15,
        )

        points_response.raise_for_status()

        points = points_response.json()

        forecast_url = points.get("properties", {}).get(
            "forecast"
        )

        if not forecast_url:
            raise NOAAAPIError(
                "NOAA did not return a forecast URL"
            )

        forecast_response = requests.get(
            forecast_url,
            headers=headers,
            timeout=15,
        )

        forecast_response.raise_for_status()

        forecast = forecast_response.json()

        periods = forecast.get(
            "properties", {}
        ).get("periods", [])

        return {
            "source": "NOAA National Weather Service",
            "location": {
                "lat": lat,
                "lon": lon,
            },
            "forecast": periods[:3],
        }

    except requests.RequestException as exc:
        raise NOAAAPIError(
            f"NOAA request failed: {exc}"
        ) from exc