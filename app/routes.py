from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from geoalchemy2.shape import from_shape
from shapely.geometry import Point
from app.db import get_db
from app.models import Checkpoint
from app.schemas import CheckpointCreate, CheckpointOut

router = APIRouter()

@router.post("/checkpoints", response_model=CheckpointOut)
async def add_checkpoint(data: CheckpointCreate, db: AsyncSession = Depends(get_db)):
    point = from_shape(Point(data.longitude, data.latitude), srid=4326)
    cp = Checkpoint(name=data.name, geom=point)
    db.add(cp)
    await db.commit()
    await db.refresh(cp)
    return cp
