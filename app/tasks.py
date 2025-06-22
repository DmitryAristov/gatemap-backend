import asyncio
from datetime import datetime, timezone
import pandas as pd
from sklearn.cluster import KMeans
from sqlalchemy import select, delete, update
from app.models import LocationPing, QueueReport, Checkpoint
from app.db import AsyncSessionLocal
from app.settings import LOCATION_ENTRY_TTL, QUEUE_REPORT_TTL, CLEANUP_INTERVAL, STATS_REFRESH_TTL
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


async def cleanup_old_data():
    while True:
        try:
            async with AsyncSessionLocal() as session:
                now = datetime.now(timezone.utc)
                location_threshold = now - LOCATION_ENTRY_TTL
                queue_threshold = now - QUEUE_REPORT_TTL

                # Удаление старых LocationPing
                loc_del_stmt = delete(LocationPing).where(LocationPing.timestamp < location_threshold)
                loc_result = await session.execute(loc_del_stmt)
                logger.info("Удалены старые координаты старше %s", location_threshold)

                # Удаление старых QueueReport
                queue_del_stmt = delete(QueueReport).where(QueueReport.submitted_at < queue_threshold)
                queue_result = await session.execute(queue_del_stmt)
                logger.info("Удалены старые опросы старше %s", queue_threshold)

                await session.commit()

        except Exception as e:
            logger.exception("Ошибка при очистке устаревших данных: %s", e)

        await asyncio.sleep(CLEANUP_INTERVAL)


async def update_checkpoint_stats():
    while True:
        try:
            async with AsyncSessionLocal() as session:
                grouped_reports = await fetch_recent_reports(session)
                now = datetime.now(timezone.utc)
                updated_count = 0

                for checkpoint_id, data in grouped_reports.items():
                    stats = calculate_main_cluster_stats(data)
                    if not stats:
                        continue

                    avg_wait, avg_queue = stats

                    await session.execute(
                        update(Checkpoint)
                        .where(Checkpoint.id == checkpoint_id)
                        .values(
                            avg_wait_time_hours=avg_wait,
                            avg_queue_size=avg_queue,
                            avg_updated_at=now
                        )
                    )

                    logger.info(
                        "[%s] Обновление КПП: %d записей, средняя задержка: %.2f ч, очередь: %d машин",
                        checkpoint_id, len(data), avg_wait, avg_queue
                    )
                    updated_count += 1

                await session.commit()
                logger.info("Обновление статистики завершено: %d КПП", updated_count)

        except Exception as e:
            logger.exception("Ошибка при обновлении статистики КПП: %s", e)

        await asyncio.sleep(STATS_REFRESH_TTL)


async def fetch_recent_reports(session):
    stmt = select(QueueReport)
    result = await session.execute(stmt)
    reports = result.scalars().all()

    grouped = defaultdict(list)
    for r in reports:
        grouped[r.checkpoint_id].append((r.waiting_time_hours, r.throughput_vehicles_per_hour))
    return grouped


def calculate_main_cluster_stats(data: list[tuple[float, int]]) -> tuple[float, float] | None:
    if len(data) < 5:
        return None

    df = pd.DataFrame(data, columns=["waiting_time_hours", "throughput"])

    try:
        X = df[["waiting_time_hours"]].to_numpy()
        kmeans = KMeans(n_clusters=2, random_state=42, n_init=10)
        labels = kmeans.fit_predict(X)

        main_cluster = pd.Series(labels).value_counts().idxmax()
        filtered = df[labels == main_cluster]

        avg_wait = filtered["waiting_time_hours"].mean()
        avg_queue = (filtered["waiting_time_hours"] * filtered["throughput"]).mean()
        return round(avg_wait, 2), round(avg_queue)
    except Exception as e:
        logger.warning("Ошибка кластеризации: %s", e)
        return None
