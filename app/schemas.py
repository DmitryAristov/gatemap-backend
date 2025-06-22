from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from datetime import datetime

class LocationData(BaseModel):
    device_id: str = Field(..., max_length=64)
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    checkpoint_id: str


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


class ProposalOut(BaseModel):
    id: str
    title: str
    description: str | None = None
    created_at: datetime
    upvotes: int
    downvotes: int


class FeedbackCreate(BaseModel):
    message: str
    tag: str
    email: EmailStr | None = None
    include_logs: bool = False


class ProposalVoteCreate(BaseModel):
    device_id: str
    vote: bool


class ProposalVoteResult(BaseModel):
    upvotes: int
    downvotes: int
