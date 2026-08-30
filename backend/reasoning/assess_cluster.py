"""
Turns the Day 9 reasoning agent (which answers one ad-hoc chat question)
into a durable per-cluster assessment.

Day 9's /chat calls retrieve_context() + assess_hazard() fresh every time
and never stores the result anywhere. That's fine for a one-off citizen
question, but the map (Day 10) needs a stored severity per cluster to
color markers by, and the Authority Agent (Day 11) needs a persisted
assessment to build a complaint from — recomputing on every request would
mean an authority complaint could show a different severity than what a
citizen saw five minutes earlier on the map, which is a bad demo look.

This module is the one place that writes to
HazardCluster.severity/explanation/recommended_action/assessed_at.
"""
from datetime import datetime, timezone

from geoalchemy2.shape import to_shape
from sqlalchemy.orm import Session

from models import HazardCluster
from reasoning.retrieval import retrieve_context
from reasoning.agent import assess_hazard, ReasoningAgentError


class ClusterNotFoundError(Exception):
    pass


# Fixed, generic question used for cluster-level (not citizen-specific)
# assessment. Keeps the reasoning agent's prompt shape identical to the
# Day 9 /chat path — same evidence rules, same JSON contract — just
# triggered on a cluster instead of a free-text citizen question.
ASSESSMENT_QUESTION = (
    "Assess the severity of this hazard cluster based on the reports "
    "and available physical/weather context. Should nearby citizens "
    "and local authorities be concerned?"
)


def assess_cluster(db: Session, cluster_id: int, radius_m: float = 500) -> HazardCluster:
    """
    Runs retrieval + reasoning for a specific cluster's location and
    persists the result onto that cluster row. Raises ClusterNotFoundError
    if the cluster doesn't exist, or ReasoningAgentError (from
    reasoning.agent) if the LLM call itself fails — callers should catch
    and translate that into an appropriate HTTP response.

    radius_m is intentionally smaller than /chat's default 5000m: an
    assessment is about THIS cluster's immediate location, not a broad
    neighborhood scan, so we don't want unrelated distant reports pulled
    into the evidence context.
    """
    cluster = db.get(HazardCluster, cluster_id)
    if not cluster:
        raise ClusterNotFoundError(f"No cluster with id={cluster_id}")

    shape = to_shape(cluster.geom)
    lat, lon = shape.y, shape.x

    context = retrieve_context(db=db, lat=lat, lon=lon, radius_m=radius_m)

    result = assess_hazard(question=ASSESSMENT_QUESTION, context=context)

    cluster.severity = result["severity"]
    cluster.explanation = result["explanation"]
    cluster.recommended_action = result["recommended_action"]
    cluster.assessed_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(cluster)

    return cluster
