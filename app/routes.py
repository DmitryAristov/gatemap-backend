from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import async_session
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import LocationEntry
from app.schemas import LocationData
import uuid
from datetime import datetime, timezone

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

@router.get("/", response_model=str)
async def get_hello_world():
    return "Hello, world!"
