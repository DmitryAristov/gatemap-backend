from datetime import timedelta

LOCATION_ENTRY_TTL = timedelta(days=2)
LOCATION_CLEANUP_TTL = 60 * 30
UPDATE_STATS_TTL = 60 * 10
STATS_VALID_PERIOD = timedelta(hours=3)