import asyncio
from fastapi import FastAPI
from app.routes import router
from app.models import Base
from app.db import engine
from app.tasks import cleanup_old_locations, update_checkpoint_stats
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    asyncio.create_task(cleanup_old_locations())
    asyncio.create_task(update_checkpoint_stats())

    yield

    # shutdown: здесь можно добавить логику остановки (если нужно)

app = FastAPI(lifespan=lifespan)

#app.add_middleware(HTTPSRedirectMiddleware)
app.include_router(router)
