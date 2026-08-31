"""
Unit tests for routing/safe_route.py. Buffer-intersection geometry is
pure and tested directly; get_safe_route is tested with mocked DB and
mocked routing-adapter calls — no live routing API or DB required.
Run with: pytest test_safe_route.py -v
"""
from unittest.mock import MagicMock, patch

import pytest

from routing.safe_route import _route_intersects_hazards, get_safe_route
from adapters.routing_adapter import RoutingAPIError


def test_route_intersects_hazards_detects_on_path():
    route = [[28.60, 77.20], [28.61, 77.21]]
    hazard_on_path = [(28.605, 77.205, 1)]
    assert _route_intersects_hazards(route, hazard_on_path) == [1]


def test_route_intersects_hazards_ignores_far_away():
    route = [[28.60, 77.20], [28.61, 77.21]]
    hazard_far = [(28.70, 77.30, 2)]
    assert _route_intersects_hazards(route, hazard_far) == []


@patch("routing.safe_route.get_route_alternatives")
@patch("routing.safe_route._get_verified_hazard_points")
def test_returns_first_clean_alternative(mock_hazards, mock_routes):
    mock_hazards.return_value = [(28.605, 77.205, 1)]  # sits on the "dirty" route
    dirty_route = {"geometry": [[28.60, 77.20], [28.61, 77.21]], "distance_m": 1000, "duration_s": 120}
    clean_route = {"geometry": [[28.60, 77.20], [28.50, 77.10]], "distance_m": 1500, "duration_s": 180}
    mock_routes.return_value = [dirty_route, clean_route]

    db = MagicMock()
    result = get_safe_route(db, 28.60, 77.20, 28.61, 77.21)

    assert result["geometry"] == clean_route["geometry"]
    assert result["warning"] is None


@patch("routing.safe_route.get_route_alternatives")
@patch("routing.safe_route._get_verified_hazard_points")
def test_warns_when_no_clean_route_exists(mock_hazards, mock_routes):
    mock_hazards.return_value = [(28.605, 77.205, 1)]
    dirty_route = {"geometry": [[28.60, 77.20], [28.61, 77.21]], "distance_m": 1000, "duration_s": 120}
    mock_routes.return_value = [dirty_route]  # only one option, and it's dirty

    db = MagicMock()
    result = get_safe_route(db, 28.60, 77.20, 28.61, 77.21)

    assert result["warning"] is not None
    assert "1" in result["warning"]


@patch("routing.safe_route.get_route_alternatives")
@patch("routing.safe_route._get_verified_hazard_points")
def test_no_hazards_returns_default_route_with_no_warning(mock_hazards, mock_routes):
    mock_hazards.return_value = []
    default_route = {"geometry": [[28.60, 77.20], [28.61, 77.21]], "distance_m": 1000, "duration_s": 120}
    mock_routes.return_value = [default_route]

    db = MagicMock()
    result = get_safe_route(db, 28.60, 77.20, 28.61, 77.21)

    assert result["warning"] is None
    assert result["avoided_hazard_ids"] == []


@patch("routing.safe_route.get_route_alternatives", side_effect=RoutingAPIError("simulated failure"))
def test_propagates_routing_api_error(mock_routes):
    db = MagicMock()
    with pytest.raises(RoutingAPIError):
        get_safe_route(db, 28.60, 77.20, 28.61, 77.21)
