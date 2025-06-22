from datetime import timedelta

LOCATION_ENTRY_TTL = timedelta(days=1)
QUEUE_REPORT_TTL = timedelta(days=1)
CLEANUP_INTERVAL = 60 * 30
STATS_REFRESH_TTL = 60 * 10