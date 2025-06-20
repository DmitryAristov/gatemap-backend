from fastapi import FastAPI
from app.routes import router
from app.models import Base
from app.db import engine

app = FastAPI()
app.include_router(router)

@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
