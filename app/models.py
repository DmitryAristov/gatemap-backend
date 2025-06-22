from sqlalchemy import Column, String, Float, Integer, DateTime, ForeignKey, Enum
from datetime import datetime, timezone
from sqlalchemy.orm import relationship, declarative_base
import enum as py_enum

Base = declarative_base()


class DirectionEnum(py_enum.Enum):
    inbound = "inbound"
    outbound = "outbound"


class LocationEntry(Base):
    __tablename__ = "location_entries"

    id = Column(String, primary_key=True)
    device_id = Column(String, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    timestamp = Column(DateTime, default=datetime.now(timezone.utc))


class Checkpoint(Base):
    __tablename__ = "checkpoints"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)
    lat = Column(Float, nullable=False)
    lon = Column(Float, nullable=False)
    country_from = Column(String)
    country_to = Column(String)
    avg_wait_time_hours = Column(Float, nullable=False)
    avg_queue_size = Column(Integer, nullable=False)
    avg_updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    
    gates = relationship("Gate", back_populates="checkpoint", cascade="all, delete-orphan")


class Gate(Base):
    __tablename__ = "gates"

    id = Column(Integer, primary_key=True, autoincrement=True)
    checkpoint_id = Column(Integer, ForeignKey("checkpoints.id", ondelete="CASCADE"), nullable=False)
    lat = Column(Float, nullable=False)
    lon = Column(Float, nullable=False)
    direction = Column(Enum(DirectionEnum), nullable=False)

    checkpoint = relationship("Checkpoint", back_populates="gates")


class QueueReport(Base):
    __tablename__ = "queue_reports"

    id = Column(String, primary_key=True)
    checkpoint_id = Column(String, nullable=False)
    lat = Column(Float, nullable=False)
    lon = Column(Float, nullable=False)
    waiting_time_hours = Column(Float, nullable=False)
    throughput_vehicles_per_hour = Column(Integer, nullable=False)
    device_id = Column(String, nullable=False)
    submitted_at = Column(DateTime, default=datetime.now(timezone.utc))
