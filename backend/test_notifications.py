"""
Unit tests for notifications/nearby_alerts.py. The distance helper is
pure and needs no mocking; get_nearby_verified_clusters is tested with
a mocked DB session. Run with: pytest test_notifications.py -v
"""
from unittest.mock import MagicMock, patch

from notifications.nearby_alerts import get_nearby_verified_clusters, _approx_distance_m


def test_distance_calc_is_reasonable():
    d = _approx_distance_m(28.60, 77.20, 28.61, 77.20)
    assert 1000 < d < 1200  # ~1.11km for 0.01 deg latitude


@patch("notifications.nearby_alerts.to_shape")
def test_get_nearby_verified_clusters_shapes_output(mock_to_shape):
    fake_cluster = MagicMock(
        id=5, category=MagicMock(value="flooding"),
        severity="High", explanation="Explanation text.",
        recommended_action="Avoid the area.", geom=MagicMock(),
    )
    mock_to_shape.return_value = MagicMock(y=28.605, x=77.205)

    db = MagicMock()
    db.execute.return_value.scalars.return_value.all.return_value = [fake_cluster]

    alerts = get_nearby_verified_clusters(db, lat=28.60, lon=77.20, radius_m=3000)

    assert len(alerts) == 1
    assert alerts[0]["cluster_id"] == 5
    assert alerts[0]["category"] == "flooding"
    assert alerts[0]["severity"] == "High"
    assert alerts[0]["distance_m"] >= 0
