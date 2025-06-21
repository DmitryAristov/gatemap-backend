from sqlalchemy import Column, String, Float, DateTime
from datetime import datetime, timezone
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class LocationEntry(Base):
    __tablename__ = "location_entries"

    id = Column(String, primary_key=True)
    device_id = Column(String, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    timestamp = Column(DateTime, default=datetime.now(timezone.utc))