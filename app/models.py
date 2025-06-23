from datetime import datetime, timezone
import uuid
from sqlalchemy import (
    Column, String, Integer, Float, DateTime, Boolean,
    ForeignKey, UniqueConstraint, Text
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class Checkpoint(Base):
    __tablename__ = "checkpoints"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=True)
    lat = Column(Float, nullable=False)
    lon = Column(Float, nullable=False)
    country_from = Column(String, nullable=True)
    country_to = Column(String, nullable=True)

    avg_wait_time_hours = Column(Float, nullable=False, default=0.0)
    avg_queue_size = Column(Integer, nullable=False, default=0)
    avg_updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    # Relationships
    reports = relationship("QueueReport", back_populates="checkpoint", cascade="all, delete-orphan")


class QueueReport(Base):
    __tablename__ = "queue_reports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    checkpoint_id = Column(Integer, ForeignKey("checkpoints.id"), nullable=False)
    lat = Column(Float, nullable=False)
    lon = Column(Float, nullable=False)
    waiting_time_hours = Column(Float, nullable=False)
    throughput_vehicles_per_hour = Column(Integer, nullable=False)
    device_id = Column(String, nullable=False)
    submitted_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    # Relationships
    checkpoint = relationship("Checkpoint", back_populates="reports")

    __table_args__ = (
        UniqueConstraint('device_id', 'checkpoint_id', name='uix_queue_device_checkpoint'),
    )


class LocationPing(Base):
    __tablename__ = "location_pings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    device_id = Column(String, nullable=False)
    lat = Column(Float, nullable=False)
    lon = Column(Float, nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    checkpoint_id = Column(Integer, ForeignKey("checkpoints.id"), nullable=True)


class Feedback(Base):
    __tablename__ = "feedback"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    message = Column(String, nullable=False)
    tag = Column(String, nullable=False)  # 'Ошибка' / 'Идея' / 'Другое'
    email = Column(String, nullable=True)
    logs = Column(Text, nullable=True)
    submitted_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))


class Proposal(Base):
    __tablename__ = "proposals"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    votes = relationship("ProposalVote", back_populates="proposal", cascade="all, delete-orphan")


class ProposalVote(Base):
    __tablename__ = "proposal_votes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    proposal_id = Column(UUID(as_uuid=True), ForeignKey("proposals.id"), nullable=False)
    device_id = Column(String, nullable=False)
    vote = Column(Boolean, nullable=False)  # True = за, False = против
    voted_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    proposal = relationship("Proposal", back_populates="votes")

    __table_args__ = (
        UniqueConstraint('proposal_id', 'device_id', name='uix_proposal_device_vote'),
    )
