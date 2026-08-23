from sqlalchemy import select
from sqlalchemy.orm import Session

from models import User, Report, HazardCluster, ClusterStatus


CANDIDATE_THRESHOLD = 25
VERIFIED_THRESHOLD = 60


def calculate_confidence(db: Session, cluster: HazardCluster) -> int:
    """
    Calculate confidence for a hazard cluster.

    Confidence is based on:
    - number of reports
    - number of unique users
    - average trust score of those users
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

    # Get unique users who submitted reports
    user_ids = {report.user_id for report in reports}

    users = (
        db.execute(
            select(User)
            .where(User.id.in_(user_ids))
        )
        .scalars()
        .all()
    )

    # Average trust score
    if users:
        average_trust = sum(
            user.trust_score for user in users
        ) / len(users)
    else:
        average_trust = 0

    report_count = len(reports)
    unique_user_count = len(user_ids)

    # Score components
    report_score = min(report_count * 10, 40)
    user_score = min(unique_user_count * 10, 30)
    trust_score = min(int(average_trust), 30)

    confidence = (
        report_score
        + user_score
        + trust_score
    )

    return min(confidence, 100)


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

    confidence = calculate_confidence(
        db,
        cluster
    )

    cluster.confidence = confidence

    if confidence >= VERIFIED_THRESHOLD:
        cluster.status = ClusterStatus.verified

    elif confidence >= CANDIDATE_THRESHOLD:
        cluster.status = ClusterStatus.candidate

    else:
        cluster.status = ClusterStatus.forming

    db.commit()
    db.refresh(cluster)

    return cluster