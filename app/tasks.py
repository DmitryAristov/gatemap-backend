import asyncio
from datetime import datetime, timezone
import pandas as pd
from sklearn.cluster import KMeans
from sqlalchemy import select, delete, update
from app.models import LocationEntry, QueueReport, Checkpoint
from app.db import AsyncSessionLocal
from app.settings import LOCATION_ENTRY_TTL, LOCATION_CLEANUP_TTL, UPDATE_STATS_TTL, STATS_VALID_PERIOD


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


async def update_checkpoint_stats():
    while True:
        try:
            async with AsyncSessionLocal() as session:
                three_hours_ago = datetime.now(timezone.utc) - STATS_VALID_PERIOD
                stmt = select(QueueReport).where(QueueReport.submitted_at >= three_hours_ago)
                result = await session.execute(stmt)
                reports = result.scalars().all()

                from collections import defaultdict
                grouped = defaultdict(list)
                for r in reports:
                    grouped[r.checkpoint_id].append((r.waiting_time_hours, r.throughput_vehicles_per_hour))

                now = datetime.now(timezone.utc)

                for checkpoint_id, data in grouped.items():
                    if len(data) < 5:
                        continue

                    df = pd.DataFrame(data, columns=["waiting_time_hours", "throughput"])

                    try:
                        X = df[["waiting_time_hours"]].to_numpy()
                        kmeans = KMeans(n_clusters=2, random_state=42, n_init=10)
                        labels = kmeans.fit_predict(X)

                        main_cluster = pd.Series(labels).value_counts().idxmax()
                        filtered = df[labels == main_cluster]

                        avg_wait = filtered["waiting_time_hours"].mean()
                        avg_queue = (filtered["waiting_time_hours"] * filtered["throughput"]).mean()

                        print(
                            f"[{checkpoint_id}] Всего записей: {len(data)}, "
                            f"в основном кластере: {len(filtered)} → "
                            f"avg_wait: {round(avg_wait, 2)} ч, "
                            f"queue_size: {round(avg_queue)} машин"
                        )

                        # Обновляем запись Checkpoint
                        await session.execute(
                            select(Checkpoint).where(Checkpoint.id == checkpoint_id).execution_options(populate_existing=True)
                        )
                        await session.execute(
                            update(Checkpoint)
                            .where(Checkpoint.id == checkpoint_id)
                            .values(
                                avg_wait_time_hours=round(avg_wait, 2),
                                avg_queue_size=round(avg_queue),
                                avg_updated_at=now
                            )
                        )

                    except Exception as e:
                        print(f"Ошибка при кластеризации {checkpoint_id}: {e}")
                        continue

                await session.commit()
            print(f"[{datetime.now().isoformat()}] Обновлено {len(grouped)} КПП")
        except Exception as e:
            print(f"[ОШИБКА] update_checkpoint_stats: {e}")
        await asyncio.sleep(UPDATE_STATS_TTL)
