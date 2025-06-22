from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class LocationData(BaseModel):
    device_id: str = Field(..., max_length=64)
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)


class CheckpointOut(BaseModel):
    id: int
    name: str
    latitude: float
    longitude: float
    country_from: str
    country_to: str
    queueSize: Optional[int] = 0
    waitTimeHours: Optional[float] = 0.0


class QueueReportCreate(BaseModel):
    checkpoint_id: str
    lat: float
    lon: float
    waiting_time_hours: float
    throughput_vehicles_per_hour: int
    device_id: str


class QueueReportOut(BaseModel):
    submitted_at: datetime
