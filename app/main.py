from fastapi import FastAPI
from app.routes import router
from app.models import Base, LocationEntry
from app.db import engine, async_session
import asyncio
from datetime import datetime, timedelta, timezone
from sqlalchemy import delete

app = FastAPI()
app.include_router(router)

@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    asyncio.create_task(cleanup_old_locations())


async def cleanup_old_locations():
    while True:
        async with async_session() as session:
            threshold = threshold = datetime.now(timezone.utc) - timedelta(days=2)
            await session.execute(
                delete(LocationEntry).where(LocationEntry.timestamp < threshold)
            )
            await session.commit()
        await asyncio.sleep(60 * 60 * 6)