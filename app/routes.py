from fastapi import APIRouter, Query, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db import async_session
from app.models import LocationEntry, Checkpoint
from app.schemas import LocationData
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


@router.get("/checkpoints/")
async def get_checkpoints_in_bbox(
    min_lat: float = Query(..., description="Минимальная широта"),
    max_lat: float = Query(..., description="Максимальная широта"),
    min_lon: float = Query(..., description="Минимальная долгота"),
    max_lon: float = Query(..., description="Максимальная долгота"),
    db: AsyncSession = Depends(async_session)
):
    stmt = select(Checkpoint).where(
        Checkpoint.lat >= min_lat,
        Checkpoint.lat <= max_lat,
        Checkpoint.lon >= min_lon,
        Checkpoint.lon <= max_lon
    )

    result = await db.execute(stmt)
    checkpoints = result.scalars().all()

    return [
        {
            "id": cp.id,
            "name": cp.name,
            "lat": cp.lat,
            "lon": cp.lon,
            "country_from": cp.country_from,
            "country_to": cp.country_to
        }
        for cp in checkpoints
    ]


@router.get("/", response_model=str)
async def get_hello_world():
    return "Hello, world!"
