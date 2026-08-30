"""
Day 11 — wires the authority agent into the DB, mirroring the same
pattern as reasoning/assess_cluster.py from Day 10: one module, one job,
called by a single endpoint in main.py.
"""
from geoalchemy2.shape import to_shape
from sqlalchemy.orm import Session

from models import HazardCluster, AuthorityComplaint, ComplaintStatus
from reasoning.retrieval import retrieve_context
from reasoning.assess_cluster import assess_cluster, ClusterNotFoundError
from reasoning.authority_agent import generate_complaint, AuthorityAgentError


def generate_complaint_for_cluster(db: Session, cluster_id: int) -> AuthorityComplaint:
    """
    If the cluster hasn't been assessed yet (severity is None), runs the
    Day 10 assessment first automatically rather than erroring — a
    complaint is meaningless without an assessment behind it, and forcing
    a manual two-step (assess, then generate-complaint) adds friction for
    no real benefit in a hackathon demo.
    """
    cluster = db.get(HazardCluster, cluster_id)
    if not cluster:
        raise ClusterNotFoundError(f"No cluster with id={cluster_id}")

    if not cluster.severity:
        cluster = assess_cluster(db, cluster_id)  # raises ReasoningAgentError on failure; let it propagate

    shape = to_shape(cluster.geom)
    context = retrieve_context(db=db, lat=shape.y, lon=shape.x, radius_m=500)

    category_value = cluster.category.value if hasattr(cluster.category, "value") else str(cluster.category)

    assessment = {
        "severity": cluster.severity,
        "explanation": cluster.explanation,
        "recommended_action": cluster.recommended_action,
    }

    result = generate_complaint(category=category_value, assessment=assessment, context=context)

    complaint = AuthorityComplaint(
        cluster_id=cluster.id,
        title=result["title"],
        description=result["description"],
        severity=result["severity"],
        recommended_action=result["recommended_action"],
        responsible_authority=result["responsible_authority"],
        status=ComplaintStatus.draft,
    )
    db.add(complaint)
    db.commit()
    db.refresh(complaint)

    return complaint