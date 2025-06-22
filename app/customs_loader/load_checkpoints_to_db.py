import json
from pathlib import Path
import asyncio

from app.db import AsyncSessionLocal
from app.models import Checkpoint
from sqlalchemy import insert

CHECKPOINTS_FILE = Path("data/osm_checkpoints_final.json")

async def import_checkpoints():
    # Загружаем JSON
    with CHECKPOINTS_FILE.open("r", encoding="utf-8") as f:
        elements = json.load(f)["elements"]

    async with AsyncSessionLocal() as session:
        for el in elements:
            lat = el.get("lat") or el.get("center", {}).get("lat")
            lon = el.get("lon") or el.get("center", {}).get("lon")
            name = el.get("tags", {}).get("name", "Unknown")
            country_from = el.get("country_match")
            country_to = el.get("country_to")

            checkpoint = Checkpoint(
                name=name,
                lat=lat,
                lon=lon,
                country_from=country_from,
                country_to=country_to
            )

            session.add(checkpoint)

        await session.commit()
        print(f"[OK] Импортировано {len(elements)} КПП в базу данных")

if __name__ == "__main__":
    asyncio.run(import_checkpoints())
