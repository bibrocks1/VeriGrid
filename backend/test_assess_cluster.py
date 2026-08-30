"""
Unit tests for reasoning/assess_cluster.py using a mocked DB session and
mocked retrieval/reasoning calls — no live DB or OpenAI key required.
Run with: pytest test_assess_cluster.py -v
"""
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from reasoning.assess_cluster import assess_cluster, ClusterNotFoundError


def test_raises_when_cluster_not_found():
    db = MagicMock()
    db.get.return_value = None

    with pytest.raises(ClusterNotFoundError):
        assess_cluster(db, cluster_id=999)


@patch("reasoning.assess_cluster.assess_hazard")
@patch("reasoning.assess_cluster.retrieve_context")
@patch("reasoning.assess_cluster.to_shape")
def test_persists_assessment_onto_cluster(mock_to_shape, mock_retrieve, mock_assess):
    fake_cluster = MagicMock(id=1, geom=MagicMock(), severity=None, explanation=None,
                              recommended_action=None, assessed_at=None)
    db = MagicMock()
    db.get.return_value = fake_cluster

    fake_shape = MagicMock(y=28.60, x=77.20)
    mock_to_shape.return_value = fake_shape

    mock_retrieve.return_value = {"verigrid": {}, "mireye": None, "noaa": None}
    mock_assess.return_value = {
        "severity": "High",
        "explanation": "Test explanation.",
        "recommended_action": "Test action.",
        "evidence_summary": {"verigrid": "x", "mireye": "y", "noaa": "z"},
    }

    result = assess_cluster(db, cluster_id=1)

    assert result.severity == "High"
    assert result.explanation == "Test explanation."
    assert result.recommended_action == "Test action."
    assert result.assessed_at is not None
    db.commit.assert_called_once()

    # Confirm retrieve_context was called with the cluster's actual
    # centroid coordinates, not hardcoded/wrong ones.
    _, kwargs = mock_retrieve.call_args
    assert kwargs["lat"] == 28.60
    assert kwargs["lon"] == 77.20
