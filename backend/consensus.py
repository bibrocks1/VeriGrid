from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from models import ClusterStatus, HazardCluster, Report, User


CANDIDATE_THRESHOLD = 25
VERIFIED_THRESHOLD = 60
TRUST_REWARD_ON_VERIFY = 2
PER_USER_TRUST_CAP = 25
TRUST_CAP = 25


def utcnow():
    return datetime.now(timezone.utc)


def compute_confidence_score(
    report_count: int,
    unique_user_count: int,
    average_trust: float
) -> int:
    """
    Pure scoring function independent of the database.
    """

    report_score = min(report_count * 10, 40)
    user_score = min(unique_user_count * 10, 30)
    trust_score = min(int(average_trust), 30)

    confidence = report_score + user_score + trust_score

    return min(confidence, 100)


def calculate_confidence(
    db: Session,
    cluster: HazardCluster
) -> int:
    """
    Calculate confidence using reports, unique contributors,
    and per-user-capped trust scores.
    """

    reports = (
        db.execute(
            select(Report)
            .where(Report.cluster_id == cluster.id)
        )
        .scalars()
        .all()
    )

    if not reports:
        return 0

    user_ids = {report.user_id for report in reports}

    users = (
        db.execute(
            select(User)
            .where(User.id.in_(user_ids))
        )
        .scalars()
        .all()
    )

    if users:
        average_trust = (
            sum(
                min(user.trust_score, PER_USER_TRUST_CAP)
                for user in users
            )
            / len(users)
        )
    else:
        average_trust = 0

    return compute_confidence_score(
        report_count=len(reports),
        unique_user_count=len(user_ids),
        average_trust=average_trust,
    )


def recompute_confidence(
    db: Session,
    cluster: HazardCluster
) -> HazardCluster:
    """
    Recompute confidence and status, and reward contributors
    when a cluster becomes verified.
    """

    reports = (
        db.execute(
            select(Report)
            .where(Report.cluster_id == cluster.id)
        )
        .scalars()
        .all()
    )

    user_ids = {report.user_id for report in reports}

    users = (
        db.execute(
            select(User)
            .where(User.id.in_(user_ids))
        )
        .scalars()
        .all()
    ) if user_ids else []

    confidence = calculate_confidence(db, cluster)

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
            user.trust_score = min(
                user.trust_score + TRUST_REWARD_ON_VERIFY,
                TRUST_CAP
            )

    return cluster


def update_cluster_confidence(
    db: Session,
    cluster_id: int
):
    """
    Calculate confidence and update cluster status.
    """

    cluster = db.get(HazardCluster, cluster_id)

    if not cluster:
        return None

    recompute_confidence(db, cluster)

    db.commit()
    db.refresh(cluster)

    return cluster