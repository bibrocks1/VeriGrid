import enum
from datetime import datetime, timezone

from geoalchemy2 import Geometry
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
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
    forming = "forming"
    candidate = "candidate"
    verified = "verified"


class ComplaintStatus(str, enum.Enum):
    draft = "draft"
    approved = "approved"
    sent = "sent"


class User(Base):
    __tablename__ = "users"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )

    trust_score = Column(
        Integer,
        default=10,
        nullable=False,
    )

    created_at = Column(
        DateTime(timezone=True),
        default=utcnow,
    )

    reports = relationship("Report", back_populates="user")

    def __repr__(self):
        return f"<User id={self.id} trust_score={self.trust_score}>"


class Report(Base):
    __tablename__ = "reports"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )

    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
    )

    category = Column(
        SAEnum(ReportCategory),
        nullable=False,
        index=True,
    )

    description = Column(
        Text,
        nullable=True,
    )

    # Keep Geometry because your existing reports.geom column
    # is Geometry in PostgreSQL.
    geom = Column(
        Geometry(geometry_type="POINT", srid=4326),
        nullable=False,
    )

    cluster_id = Column(
        Integer,
        ForeignKey("hazard_clusters.id"),
        nullable=True,
        index=True,
    )

    created_at = Column(
        DateTime(timezone=True),
        default=utcnow,
    )

    user = relationship(
        "User",
        back_populates="reports",
    )

    cluster = relationship(
        "HazardCluster",
        back_populates="reports",
    )

    def __repr__(self):
        return f"<Report id={self.id} category={self.category} user_id={self.user_id}>"


class HazardCluster(Base):
    __tablename__ = "hazard_clusters"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    category = Column(
        SAEnum(ReportCategory),
        nullable=False,
        index=True,
    )

    # Keep Geometry because your existing hazard_clusters.geom
    # is also stored as Geometry in your current database.
    geom = Column(
        Geometry(geometry_type="POINT", srid=4326),
        nullable=False,
    )

    status = Column(
        SAEnum(ClusterStatus),
        nullable=False,
        default=ClusterStatus.forming,
        index=True,
    )

    confidence = Column(
        Integer,
        nullable=False,
        default=0,
    )

    report_count = Column(
        Integer,
        nullable=False,
        default=0,
    )

    created_at = Column(
        DateTime(timezone=True),
        default=utcnow,
    )

    updated_at = Column(
        DateTime(timezone=True),
        default=utcnow,
        onupdate=utcnow,
    )

    verified_at = Column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Reasoning-agent assessment
    severity = Column(
        String(20),
        nullable=True,
    )

    explanation = Column(
        Text,
        nullable=True,
    )

    recommended_action = Column(
        Text,
        nullable=True,
    )

    assessed_at = Column(
        DateTime(timezone=True),
        nullable=True,
    )

    reports = relationship(
        "Report",
        back_populates="cluster",
    )

    def __repr__(self):
        return f"<HazardCluster id={self.id} status={self.status} confidence={self.confidence}>"


class AuthorityComplaint(Base):
    __tablename__ = "authority_complaints"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    cluster_id = Column(
        Integer,
        ForeignKey("hazard_clusters.id"),
        nullable=False,
        index=True,
    )

    title = Column(
        String(255),
        nullable=False,
    )

    description = Column(
        Text,
        nullable=False,
    )

    severity = Column(
        String(20),
        nullable=True,
    )

    recommended_action = Column(
        Text,
        nullable=True,
    )

    responsible_authority = Column(
        String(255),
        nullable=False,
    )

    status = Column(
        SAEnum(ComplaintStatus),
        nullable=False,
        default=ComplaintStatus.draft,
        index=True,
    )

    created_at = Column(
        DateTime(timezone=True),
        default=utcnow,
    )

    approved_at = Column(
        DateTime(timezone=True),
        nullable=True,
    )

    sent_at = Column(
        DateTime(timezone=True),
        nullable=True,
    )

    cluster = relationship(
        "HazardCluster",
    )

    def __repr__(self):
        return (
            f"<AuthorityComplaint "
            f"id={self.id} "
            f"cluster_id={self.cluster_id} "
            f"status={self.status}>"
        )