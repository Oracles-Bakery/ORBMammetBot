# utils/app/status.py
import utils.database.postgres as postgres
from datetime import datetime, timezone

async def write_status(status: str, reason: str | None = None):
    query = """
    INSERT INTO bot_status (status, last_heartbeat, reason)
    VALUES ($1, $2, $3)
    """
    now = datetime.now(timezone.utc)
    await postgres.execute(query, status, now, reason)