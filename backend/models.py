import enum
from datetime import datetime, timezone

from geoalchemy2 import Geography
from sqlalchemy import Column, DateTime, ForeignKey, Integer
from sqlalchemy import Enum as SAEnum
from sqlalchemy import Text
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


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    trust_score = Column(Integer, nullable=False, default=10)
    created_at = Column(DateTime(timezone=True), default=utcnow)

    reports = relationship("Report", back_populates="user")

    def __repr__(self):
        return f"<User id={self.id} trust_score={self.trust_score}>"


class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    category = Column(SAEnum(ReportCategory), nullable=False, index=True)
    description = Column(Text, nullable=True)

    # Geography (not Geometry) so ST_DWithin / ST_Distance return real meters,
    # not degrees. SRID 4326 = standard lat/lon (WGS84).
    geom = Column(Geography(geometry_type="POINT", srid=4326), nullable=False)

    # Nullable: a report starts unclustered, DBSCAN assigns this on Day 6.
    cluster_id = Column(Integer, ForeignKey("hazard_clusters.id"), nullable=True, index=True)

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

    reports = relationship("Report", back_populates="cluster")

    def __repr__(self):
        return f"<HazardCluster id={self.id} status={self.status} confidence={self.confidence}>"