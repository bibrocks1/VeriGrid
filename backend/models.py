import enum
from datetime import datetime, timezone

from geoalchemy2 import Geography
from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import relationship

from database import Base

def utcnow():
    return datetime.now(timezone.utc)


class ReportCategory(str, enum.Enum):
    flooding = "flooding"
    waterlogging = "waterlogging"
    road_damage = "road_damage"
    construction = "construction"
    safety = "safety"
    environmental = "environmental"
    traffic = "traffic"
    other = "other"


class ClusterStatus(str, enum.Enum):
    forming = "forming"      # fewer than 3 corroborating reports, not clustered yet
    candidate = "candidate"  # confidence >= 25
    verified = "verified"    # confidence >= 60, pushed to MirEye

class ComplaintStatus(str, enum.Enum):
    draft = "draft"
    approved = "approved"
    sent = "sent"

class User(Base):
    __tablename__ = "users"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()")
    )

    # Identifies an anonymous browser (localStorage-generated UUID, see
    # frontend/src/lib/deviceId.js) as "the same reporter" across visits.
    # No login system exists — this is the whole identity model. Reconciled
    # in from the Frontend branch: main's schema previously required an
    # already-existing user_id on every report, with no way for a new
    # anonymous visitor to become a user in the first place.
    device_id = Column(String, unique=True, nullable=True, index=True)

    trust_score = Column(
        Float,
        default=10.0,
        nullable=False
    )
    created_at = Column(DateTime(timezone=True), default=utcnow)

    reports = relationship("Report", back_populates="user")

    def __repr__(self):
        return f"<User id={self.id} trust_score={self.trust_score}>"


class Report(Base):
    __tablename__ = "reports"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()")
    )

    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False
    )

    category = Column(SAEnum(ReportCategory), nullable=False, index=True)
    description = Column(Text, nullable=True)

    # Geography (not Geometry): ST_DWithin / ST_Distance need this to return
    # real meters, not degrees. Geometry was tried in an earlier main
    # commit and produced wrong radius results (radius_m was silently being
    # read as ~radius_m degrees) — reconciled back to Geography here.
    # SRID 4326 = standard lat/lon (WGS84).
    geom = Column(Geography(geometry_type="POINT", srid=4326), nullable=False)

    # Nullable: a report starts unclustered, DBSCAN assigns this on Day 6.
    cluster_id = Column(Integer, ForeignKey("hazard_clusters.id"), nullable=True, index=True)

    # MirEye terrain/hazard context checked against the report's own category
    # at submission time. Nullable: stays unset if MirEye is unreachable or
    # the category has no mapped preset — advisory only, never blocks
    # report creation.
    mireye_credibility_score = Column(Integer, nullable=True)
    mireye_credibility_notes = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), default=utcnow)

    user = relationship("User", back_populates="reports")
    cluster = relationship("HazardCluster", back_populates="reports")

    def __repr__(self):
        return f"<Report id={self.id} category={self.category} user_id={self.user_id}>"


class HazardCluster(Base):
    __tablename__ = "hazard_clusters"

    id = Column(Integer, primary_key=True, index=True)
    category = Column(SAEnum(ReportCategory), nullable=False, index=True)

    # Centroid of all member reports, recomputed whenever a report joins the cluster.
    geom = Column(Geography(geometry_type="POINT", srid=4326), nullable=False)

    status = Column(SAEnum(ClusterStatus), nullable=False, default=ClusterStatus.forming, index=True)
    confidence = Column(Integer, nullable=False, default=0)
    report_count = Column(Integer, nullable=False, default=0)

    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    # Set once, the first time this cluster's status becomes verified.
    verified_at = Column(DateTime(timezone=True), nullable=True)

    reports = relationship("Report", back_populates="cluster")

    # Day 9/10 reasoning-agent assessment (VeriGrid + MirEye + NOAA evidence),
    # persisted so the map and an authority complaint always agree on
    # severity instead of recomputing it differently each time.
    severity = Column(String(20), nullable=True)
    explanation = Column(Text, nullable=True)
    recommended_action = Column(Text, nullable=True)
    assessed_at = Column(DateTime(timezone=True), nullable=True)

    def __repr__(self):
        return f"<HazardCluster id={self.id} status={self.status} confidence={self.confidence}>"

class AuthorityComplaint(Base):
    __tablename__ = "authority_complaints"

    id = Column(Integer, primary_key=True, index=True)
    cluster_id = Column(Integer, ForeignKey("hazard_clusters.id"), nullable=False, unique=True, index=True)

    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    severity = Column(String(20), nullable=True)
    recommended_action = Column(Text, nullable=True)
    responsible_authority = Column(String(255), nullable=False)

    # Doc's Day 11 spec (structured dict fields) that main's original
    # version didn't persist — needed by AuthorityReportCard.jsx on the
    # frontend, computed from the cluster/its member reports at generation
    # time rather than asked of the LLM.
    location = Column(String(255), nullable=True)
    confidence = Column(Integer, nullable=True)
    contributor_count = Column(Integer, nullable=True)

    status = Column(SAEnum(ComplaintStatus), nullable=False, default=ComplaintStatus.draft, index=True)
    delivery_detail = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), default=utcnow)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    sent_at = Column(DateTime(timezone=True), nullable=True)

    cluster = relationship("HazardCluster")

    def __repr__(self):
        return f"<AuthorityComplaint id={self.id} cluster_id={self.cluster_id} status={self.status}>"


class MireyeSyncLog(Base):
    """Every real call out to the MirEye API, successful or not. MirEye's
    documented API has no observation-write endpoint (see
    adapters/mireye_adapter.push_verified_observation), so this logs the
    read calls actually made: report-credibility checks, chat-context
    lookups, and the "would push on verify" event from consensus.py."""

    __tablename__ = "mireye_sync_log"

    id = Column(Integer, primary_key=True, index=True)
    kind = Column(String, nullable=False)  # "report_credibility" | "chat_context" | "verified_push"
    lat = Column(Float, nullable=False)
    lng = Column(Float, nullable=False)
    status = Column(String, nullable=False)  # "ok" | "failed" | "skipped"
    detail = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, index=True)
