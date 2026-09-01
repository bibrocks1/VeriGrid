from datetime import datetime, timezone

from geoalchemy2.shape import to_shape
from sqlalchemy.orm import Session

from models import ClusterStatus, HazardCluster, MireyeSyncLog, Report, User

# Mirrors frontend/src/lib/constants.js CONFIDENCE_THRESHOLDS exactly — keep
# the two in sync if either changes.
CANDIDATE_THRESHOLD = 25
VERIFIED_THRESHOLD = 60
TRUST_REWARD_ON_VERIFY = 2
TRUST_CAP = 25

# A single high-trust user shouldn't be able to single-handedly push a
# cluster's confidence up by having an outsized trust_score — cap each
# user's contribution before averaging. (Previously this cap existed
# only in the design notes, not in the code: the average was computed
# from raw, uncapped trust_score values.)
PER_USER_TRUST_CAP = 25


def compute_confidence_score(report_count: int, unique_user_count: int, average_trust: float) -> int:
    """
    Pure scoring function, independent of the DB — takes already-computed
    aggregates and returns a 0-100 confidence score. Extracted so this
    logic can be unit tested without a database (see test_consensus.py).
    """
    report_score = min(report_count * 10, 40)
    user_score = min(unique_user_count * 10, 30)
    trust_score = min(int(average_trust), 30)

    confidence = report_score + user_score + trust_score
    return min(confidence, 100)


def utcnow():
    return datetime.now(timezone.utc)


def recompute_confidence(db: Session, cluster: HazardCluster) -> HazardCluster:
    """Recompute a cluster's confidence/status from its current members.

    Per the doc's Day 7 spec: dedup contributors by user_id first — this is
    what stops one person from inflating a cluster's confidence by
    reporting the same hazard repeatedly. Each distinct user contributes
    min(trust_score, 25). A previous version of this formula on main used
    report_count/user_count/avg_trust instead, which let a single user
    hit "verified" by spamming the same report ~10 times — the exact
    failure mode this dedup step exists to prevent (see Day 13 test #2).
    """
    reports = db.query(Report).filter(Report.cluster_id == cluster.id).all()
    distinct_user_ids = {r.user_id for r in reports}
    users = db.query(User).filter(User.id.in_(distinct_user_ids)).all() if distinct_user_ids else []

    confidence = round(sum(min(u.trust_score, TRUST_CAP) for u in users))

    if confidence >= VERIFIED_THRESHOLD:
        new_status = ClusterStatus.verified
    elif confidence >= CANDIDATE_THRESHOLD:
        new_status = ClusterStatus.candidate
    else:
        new_status = ClusterStatus.forming

    was_verified = cluster.status == ClusterStatus.verified
    cluster.confidence = confidence
    cluster.report_count = len(reports)
    cluster.status = new_status
    cluster.updated_at = utcnow()

    if new_status == ClusterStatus.verified and not was_verified:
        cluster.verified_at = utcnow()
        for user in users:
            user.trust_score = min(user.trust_score + TRUST_REWARD_ON_VERIFY, TRUST_CAP)

        # Day 8's "push verified clusters to MirEye" trigger. MirEye's
        # documented API has no write endpoint (see adapters/mireye_adapter
        # .push_verified_observation), so this logs the attempt as skipped
        # rather than doing nothing silently.
        point = to_shape(cluster.geom)
        db.add(
            MireyeSyncLog(
                kind="verified_push",
                lat=point.y,
                lng=point.x,
                status="skipped",
                detail=(
                    f"cluster {cluster.id} ({cluster.category.value}) reached verified "
                    "status; MirEye has no observation-write endpoint to push to"
                ),
            )
        )

    return cluster


def update_cluster_confidence(db: Session, cluster_id: int):
    """Kept for callers (clustering.py) that only have the id, not the
    loaded row. Commits, unlike recompute_confidence which leaves
    committing to its caller (clustering.py batches several clusters into
    one commit)."""
    cluster = db.get(HazardCluster, cluster_id)
    if not cluster:
        return None
    recompute_confidence(db, cluster)
    db.commit()
    db.refresh(cluster)
    return cluster
