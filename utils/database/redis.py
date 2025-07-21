# utils/database/redis.py
import redis.asyncio as redis
import settings 


# One shared connection pool for the whole bot process
redis_pool: redis.Redis = redis.from_url(
    settings.REDIS_URL,
    decode_responses=True,     # store plain str values, not bytes
)


# helpers to manage verification tokens in Redis
async def set_verification(user_id: int, token: str, ttl: int = 600) -> None:
    """Save token ↔ user mapping for <ttl> seconds."""
    await redis_pool.setex(f"verify:{user_id}", ttl, token)

async def get_verification(user_id: int) -> str | None:
    """Return the stored token (or None) for this Discord user."""
    return await redis_pool.get(f"verify:{user_id}")

async def delete_verification(user_id: int) -> None:
    await redis_pool.delete(f"verify:{user_id}")