"""Backend-side wiring around adapters/mireye_adapter.py: which preset a
report category maps to, a lightweight plausibility score from the
returned fields, and a log row for every real call (Day 8's spirit,
adapted — MirEye's API has no write/push endpoint, so this logs the reads
we actually make instead of pushes we can't)."""

import json
from datetime import datetime, timezone
from typing import Any

from geoalchemy2.shape import to_shape
from sqlalchemy.orm import Session

from adapters.mireye_adapter import MireyeAPIError, get_area_context
from models import HazardCluster, MireyeSyncLog, Report, ReportCategory

# Which MirEye preset gives the most relevant signal for each report
# category. Categories with no strong geospatial signal (road_damage,
# construction, traffic, other) fall back to "terrain" for general context
# rather than a preset that wouldn't apply.
CATEGORY_PRESET: dict[ReportCategory, str] = {
    ReportCategory.flooding: "flood_risk",
    ReportCategory.waterlogging: "flood_risk",
    ReportCategory.safety: "natural_hazard",
    ReportCategory.environmental: "natural_hazard",
    ReportCategory.road_damage: "terrain",
    ReportCategory.construction: "terrain",
    ReportCategory.traffic: "terrain",
    ReportCategory.other: "terrain",
}


def _field_value(context: dict[str, Any], field: str) -> Any:
    return context.get("fields", {}).get(field, {}).get("value")


def fetch_area_context(
    db: Session,
    lat: float,
    lng: float,
    preset: str,
    kind: str,
) -> dict[str, Any] | None:
    """Calls MirEye and logs the attempt. Never raises — a MirEye outage
    should never block a report submission or a chat answer, it just means
    that signal is missing for this call."""
    try:
        context = get_area_context(lat, lng, preset=preset)
        db.add(MireyeSyncLog(kind=kind, lat=lat, lng=lng, status="ok", detail=preset))
        return context
    except (MireyeAPIError, ValueError) as exc:
        db.add(MireyeSyncLog(kind=kind, lat=lat, lng=lng, status="failed", detail=str(exc)[:500]))
        return None


def score_report_credibility(
    category: ReportCategory,
    context: dict[str, Any] | None,
) -> tuple[int | None, str | None]:
    """A simple, explainable plausibility score (0-100) for a report given
    MirEye's terrain/hazard context at that coordinate. Not a fraud
    detector — just a signal for whether the physical setting is
    consistent with the reported hazard, surfaced to reviewers."""
    if context is None:
        return None, None

    if category in (ReportCategory.flooding, ReportCategory.waterlogging):
        score = 40
        notes = []
        if _field_value(context, "within_floodplain_polygon"):
            score += 30
            notes.append("coordinate is within a FEMA floodplain")
        nearest_wetland_m = _field_value(context, "nearest_wetland_distance_m")
        if isinstance(nearest_wetland_m, (int, float)) and nearest_wetland_m < 200:
            score += 15
            notes.append(f"{round(nearest_wetland_m)}m from a mapped wetland")
        elevation = _field_value(context, "elevation")
        if isinstance(elevation, (int, float)) and elevation < 10:
            score += 15
            notes.append(f"low elevation ({round(elevation, 1)}m)")
        if not notes:
            notes.append("no floodplain, wetland, or low-elevation signal found nearby")
        return min(score, 100), "; ".join(notes)

    if category in (ReportCategory.safety, ReportCategory.environmental):
        score = 50
        notes = []
        landslide = _field_value(context, "landslide_susceptibility_index")
        if isinstance(landslide, (int, float)) and landslide >= 0.5:
            score += 20
            notes.append(f"elevated landslide susceptibility ({round(landslide, 2)})")
        wildfire_freq = _field_value(context, "wildfire_annual_frequency")
        if isinstance(wildfire_freq, (int, float)) and wildfire_freq > 0:
            score += 15
            notes.append("in a mapped wildfire-frequency zone")
        if not notes:
            notes.append("no elevated hazard-frequency signal found nearby")
        return min(score, 100), "; ".join(notes)

    # road_damage / construction / traffic / other: MirEye's presets don't
    # carry a direct signal for these, so no score is asserted rather than
    # fabricating one from an unrelated field.
    return None, "no MirEye preset maps to this category"


def build_verified_observation_payload(cluster: HazardCluster, members: list[Report]) -> dict[str, Any]:
    """Day 8: 'format the payload to match MirEye's real schema.' There's
    no published write-endpoint schema to match (confirmed live against
    the actual API — see push_verified_observation), so this is our best-
    effort shape for a geospatial hazard observation: close to what
    push_verified_observation(payload) would need to send verbatim the
    moment MirEye exposes a write endpoint. Built and stored in full
    regardless, rather than only recording that a push *would* happen."""
    point = to_shape(cluster.geom)
    distinct_reporters = len({r.user_id for r in members})
    first_reported_at = min((r.created_at for r in members), default=cluster.created_at)

    return {
        "source": "VeriGrid",
        "observation_type": "verified_hazard_cluster",
        "category": cluster.category.value,
        "location": {"lat": point.y, "lng": point.x},
        "confidence": cluster.confidence,
        "distinct_reporters": distinct_reporters,
        "report_count": cluster.report_count,
        "first_reported_at": first_reported_at.isoformat() if first_reported_at else None,
        "verified_at": (cluster.verified_at or datetime.now(timezone.utc)).isoformat(),
        "description": members[0].description if members else None,
    }


def log_verified_push(db: Session, cluster: HazardCluster, members: list[Report]) -> None:
    """Builds the full push payload and persists it against this cluster
    (MireyeSyncLog.cluster_id), so it's inspectable via
    GET /clusters/{id}/mireye-payload rather than existing only as a
    sentence in an undifferentiated log. Status stays "skipped" because
    nothing was actually sent over the network — MirEye has no write
    endpoint — but every field MirEye would need is already computed and
    ready."""
    point = to_shape(cluster.geom)
    payload = build_verified_observation_payload(cluster, members)
    db.add(
        MireyeSyncLog(
            kind="verified_push",
            lat=point.y,
            lng=point.x,
            status="skipped",
            detail=json.dumps(payload),
            cluster_id=cluster.id,
        )
    )
