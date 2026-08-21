from datetime import datetime, timezone

from sqlalchemy.orm import Session

from models import ClusterStatus, HazardCluster, Report, User

# Mirrors frontend/src/lib/constants.js CONFIDENCE_THRESHOLDS exactly — keep
# the two in sync if either changes.
CANDIDATE_THRESHOLD = 25
VERIFIED_THRESHOLD = 60
TRUST_REWARD_ON_VERIFY = 2
TRUST_CAP = 25


def utcnow():
    return datetime.now(timezone.utc)


def recompute_confidence(db: Session, cluster: HazardCluster) -> HazardCluster:
    """Recompute a cluster's confidence/status from its current members.

    Dedups contributors by user_id first — this is what stops one person
    from inflating a cluster's confidence by reporting the same hazard
    repeatedly. Each distinct user contributes min(trust_score, 25).
    """
    reports = db.query(Report).filter(Report.cluster_id == cluster.id).all()
    distinct_user_ids = {r.user_id for r in reports}
    users = db.query(User).filter(User.id.in_(distinct_user_ids)).all() if distinct_user_ids else []

    confidence = sum(min(u.trust_score, TRUST_CAP) for u in users)

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

    return cluster
