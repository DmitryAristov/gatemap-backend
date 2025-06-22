from fastapi import FastAPI
from app.routes import router
from app.models import Base, LocationEntry
from app.db import engine, AsyncSessionLocal
import asyncio
from datetime import datetime, timezone
from sqlalchemy import delete
from app.settings import LOCATION_ENTRY_TTL, LOCATION_CLEANUP_TTL

app = FastAPI()
app.include_router(router)

@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    asyncio.create_task(cleanup_old_locations())


async def cleanup_old_locations():
    while True:
        try:
            async with AsyncSessionLocal() as session:
                threshold = threshold = datetime.now(timezone.utc) - LOCATION_ENTRY_TTL
                await session.execute(
                    delete(LocationEntry).where(LocationEntry.timestamp < threshold)
                )
                await session.commit()
        except Exception as e:
            print(f"[CLEANUP ERROR] {e}")
        await asyncio.sleep(LOCATION_CLEANUP_TTL)