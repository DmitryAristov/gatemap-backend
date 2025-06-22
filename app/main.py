import asyncio
from fastapi import FastAPI
from app.routes import router
from app.tasks import cleanup_old_data, update_checkpoint_stats
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from contextlib import asynccontextmanager
from alembic.config import Config
from alembic import command
import logging

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        run_migrations()
    except Exception as e:
        logger.exception("Failed to apply Alembic migrations")
        raise
    asyncio.create_task(cleanup_old_data())
    asyncio.create_task(update_checkpoint_stats())

    yield

    # shutdown: здесь можно добавить логику остановки (если нужно)

app = FastAPI(lifespan=lifespan)

#app.add_middleware(HTTPSRedirectMiddleware)
app.include_router(router)


def run_migrations():
    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, "head")