"""
Unit tests for reasoning/generate_complaint_for_cluster.py using a
mocked DB session and mocked retrieval/assessment/authority-agent calls
— no live DB or OpenAI key required.
Run with: pytest test_generate_complaint_for_cluster.py -v
"""
from unittest.mock import MagicMock, patch

import pytest

from reasoning.generate_complaint_for_cluster import generate_complaint_for_cluster
from reasoning.assess_cluster import ClusterNotFoundError


def test_raises_when_cluster_not_found():
    db = MagicMock()
    db.get.return_value = None
    with pytest.raises(ClusterNotFoundError):
        generate_complaint_for_cluster(db, cluster_id=999)


@patch("reasoning.generate_complaint_for_cluster.generate_complaint")
@patch("reasoning.generate_complaint_for_cluster.retrieve_context")
@patch("reasoning.generate_complaint_for_cluster.to_shape")
def test_uses_existing_assessment_without_reassessing(mock_to_shape, mock_retrieve, mock_generate):
    # Cluster already has a severity set -> assess_cluster should NOT be called.
    fake_cluster = MagicMock(
        id=1, severity="High", explanation="already assessed",
        recommended_action="already have an action", geom=MagicMock(),
        category=MagicMock(value="flooding"),
    )
    db = MagicMock()
    db.get.return_value = fake_cluster
    mock_to_shape.return_value = MagicMock(y=28.60, x=77.20)
    mock_retrieve.return_value = {"verigrid": {}, "mireye": None, "noaa": None}
    mock_generate.return_value = {
        "title": "Test complaint",
        "description": "Test description",
        "severity": "High",
        "recommended_action": "Fix it",
        "responsible_authority": "Test Authority",
    }

    with patch("reasoning.generate_complaint_for_cluster.assess_cluster") as mock_assess:
        complaint = generate_complaint_for_cluster(db, cluster_id=1)
        mock_assess.assert_not_called()  # already assessed, should be skipped

    assert complaint.title == "Test complaint"
    assert complaint.responsible_authority == "Test Authority"
    db.add.assert_called_once()
    db.commit.assert_called_once()


@patch("reasoning.generate_complaint_for_cluster.generate_complaint")
@patch("reasoning.generate_complaint_for_cluster.retrieve_context")
@patch("reasoning.generate_complaint_for_cluster.to_shape")
@patch("reasoning.generate_complaint_for_cluster.assess_cluster")
def test_auto_assesses_unassessed_cluster_first(mock_assess, mock_to_shape, mock_retrieve, mock_generate):
    unassessed_cluster = MagicMock(id=2, severity=None, geom=MagicMock())
    assessed_cluster = MagicMock(
        id=2, severity="Medium", explanation="now assessed",
        recommended_action="now have an action", geom=MagicMock(),
        category=MagicMock(value="road_damage"),
    )
    db = MagicMock()
    db.get.return_value = unassessed_cluster
    mock_assess.return_value = assessed_cluster
    mock_to_shape.return_value = MagicMock(y=28.60, x=77.20)
    mock_retrieve.return_value = {}
    mock_generate.return_value = {
        "title": "t", "description": "d", "severity": "Medium",
        "recommended_action": "a", "responsible_authority": "Public Works",
    }

    complaint = generate_complaint_for_cluster(db, cluster_id=2)

    mock_assess.assert_called_once_with(db, 2)
    assert complaint.severity == "Medium"