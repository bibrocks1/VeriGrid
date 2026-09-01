"""
Unit tests for routing/safe_route.py. get_safe_route is tested with a
mocked routing-adapter and a mocked hazard-lookup (which itself is a real
PostGIS query — see test_database_clustering-style tests for the query
itself against a live DB; this file mocks it out entirely, no live DB
required). Run with: pytest test_safe_route.py -v
"""
from unittest.mock import MagicMock, patch

import pytest

from adapters.routing_adapter import RoutingAPIError
from routing.safe_route import get_safe_route


def _route(geometry, distance_m=1000, duration_s=120):
    return {"geometry": geometry, "distance_m": distance_m, "duration_s": duration_s, "steps": []}


@patch("routing.safe_route.get_route_alternatives")
@patch("routing.safe_route._hazards_near_route")
def test_returns_first_clean_alternative(mock_hazards, mock_routes):
    dirty_route = _route([[28.60, 77.20], [28.61, 77.21]])
    clean_route = _route([[28.60, 77.20], [28.50, 77.10]], distance_m=1500, duration_s=180)
    mock_routes.return_value = [dirty_route, clean_route]
    # Called once per alternative, in order: dirty has a hazard, clean doesn't.
    mock_hazards.side_effect = [
        [{"clusterId": 1, "category": "flooding", "lat": 28.605, "lng": 77.205, "distanceM": 10, "confidence": 70}],
        [],
    ]

    db = MagicMock()
    result = get_safe_route(db, 28.60, 77.20, 28.61, 77.21)

    assert result["geometry"] == clean_route["geometry"]
    assert result["warning"] is None
    assert result["hazardWarnings"] == []


@patch("routing.safe_route.get_route_alternatives")
@patch("routing.safe_route._hazards_near_route")
def test_warns_when_no_clean_route_exists(mock_hazards, mock_routes):
    dirty_route = _route([[28.60, 77.20], [28.61, 77.21]])
    mock_routes.return_value = [dirty_route]  # only one option, and it's dirty
    hazard = {"clusterId": 1, "category": "flooding", "lat": 28.605, "lng": 77.205, "distanceM": 10, "confidence": 70}
    mock_hazards.return_value = [hazard]

    db = MagicMock()
    result = get_safe_route(db, 28.60, 77.20, 28.61, 77.21)

    assert result["warning"] is not None
    assert result["hazardWarnings"] == [hazard]


@patch("routing.safe_route.get_route_alternatives")
@patch("routing.safe_route._hazards_near_route")
def test_no_hazards_returns_default_route_with_no_warning(mock_hazards, mock_routes):
    default_route = _route([[28.60, 77.20], [28.61, 77.21]])
    mock_routes.return_value = [default_route]
    mock_hazards.return_value = []

    db = MagicMock()
    result = get_safe_route(db, 28.60, 77.20, 28.61, 77.21)

    assert result["warning"] is None
    assert result["hazardWarnings"] == []


@patch("routing.safe_route.get_route_alternatives", side_effect=RoutingAPIError("simulated failure"))
def test_propagates_routing_api_error(mock_routes):
    db = MagicMock()
    with pytest.raises(RoutingAPIError):
        get_safe_route(db, 28.60, 77.20, 28.61, 77.21)
