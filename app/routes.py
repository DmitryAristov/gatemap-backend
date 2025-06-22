from fastapi import APIRouter, Query, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert
from app.db import async_session
from app.models import LocationEntry, Checkpoint, QueueReport
from app.schemas import LocationData, CheckpointOut, QueueReportCreate, QueueReportOut
from datetime import datetime, timezone
import uuid

router = APIRouter()


@router.post("/location")
async def save_location(data: LocationData, session: AsyncSession = Depends(async_session)):
    new_entry = LocationEntry(
        id=str(uuid.uuid4()),
        device_id=data.device_id,
        latitude=data.latitude,
        longitude=data.longitude,
        timestamp=datetime.now(timezone.utc)
    )
    session.add(new_entry)
    await session.commit()
    return {"status": "ok"}


@router.get("/checkpoints/", response_model=list[CheckpointOut])
async def get_checkpoints_in_bbox(
    min_lat: float = Query(..., description="Минимальная широта"),
    max_lat: float = Query(..., description="Максимальная широта"),
    min_lon: float = Query(..., description="Минимальная долгота"),
    max_lon: float = Query(..., description="Максимальная долгота"),
    db: AsyncSession = Depends(async_session)
):
    # Получаем КПП в bbox
    stmt = select(Checkpoint).where(
        Checkpoint.lat >= min_lat,
        Checkpoint.lat <= max_lat,
        Checkpoint.lon >= min_lon,
        Checkpoint.lon <= max_lon
    )
    result = await db.execute(stmt)
    checkpoints = result.scalars().all()

    # Объединяем и возвращаем с полями статистики из Checkpoint
    return [
        CheckpointOut(
            id=cp.id,
            name=cp.name,
            latitude=cp.lat,
            longitude=cp.lon,
            country_from=cp.country_from,
            country_to=cp.country_to,
            queueSize=cp.avg_queue_size,
            waitTimeHours=cp.avg_wait_time_hours
        )
        for cp in checkpoints
    ]



@router.post("/queue_report", response_model=QueueReportOut)
async def submit_queue_report(
    report: QueueReportCreate,
    session: AsyncSession = Depends(async_session)
):
    submitted_at = datetime.now(timezone.utc)
    new_entry = QueueReport(
        id=str(uuid.uuid4()),
        checkpoint_id=report.checkpoint_id,
        lat=report.lat,
        lon=report.lon,
        waiting_time_hours=report.waiting_time_hours,
        throughput_vehicles_per_hour=report.throughput_vehicles_per_hour,
        device_id=report.device_id,
        submitted_at=submitted_at
    )
    session.add(new_entry)
    await session.commit()
    return QueueReportOut(
        submitted_at=submitted_at
    )


@router.get("/", response_model=str)
async def get_hello_world():
    return "Hello, world!"
