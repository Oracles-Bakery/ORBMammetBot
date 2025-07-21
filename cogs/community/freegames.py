# cogs/community/freegames.py
import asyncio, json, discord, logging, datetime
from discord.ext import commands

from settings import CHANNEL_FREEGAMES
from utils.discord.embeds import base_embed
from utils.database.redis import redis_pool
from utils.colour import hex_to_discord_color

log = logging.getLogger(__name__)

class RedisListener(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.channel_id = CHANNEL_FREEGAMES
        self._redis_task = None
        self._stop_event = asyncio.Event()

    async def redis_listener(self):
        try:
            pubsub = redis_pool.pubsub()
            await pubsub.subscribe("freestuff")
            log.exception("Subscribed to Redis channel: freestuff")

            while not self._stop_event.is_set():
                message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
                if message:
                    log.exception("Received Redis message:", message)
                    try:
                        event = json.loads(message["data"])
                        await self.handle_freestuff_event(event)
                    except Exception as e:
                        log.exception("Error processing Redis message:", e)
                await asyncio.sleep(0.2)
        except Exception as e:
            log.exception("Redis listener failed:", e)

    async def process_queue(self):
        events = await redis_pool.lrange("freestuff_queue", 0, -1) # type: ignore 
        for msg in reversed(events):
            try:
                event = json.loads(msg)
                await self.handle_freestuff_event(event)
            except Exception as e:
                log.exception(f"Failed to process queued event: {e}")

    async def handle_freestuff_event(self, event):
        channel = self.bot.get_channel(self.channel_id)
        if not channel:
            log.exception("Discord channel not found!")
            return

        title = event.get("title", "Free Game!")
        description = event.get("description", "")
        url = None
        if event.get("urls"):
            first_url = event["urls"][0]
            url = first_url.get("url") if isinstance(first_url, dict) else first_url
        elif "url" in event:
            url = event["url"]

        store = ", ".join(event.get("platforms", [])) if "platforms" in event else event.get("platform", "Unknown")

        image_url = None
        if event.get("images"):
            first_img = event["images"][0]
            image_url = first_img.get("url") if isinstance(first_img, dict) else first_img
        elif "image_url" in event:
            image_url = event["image_url"]

        # price formatting
        price_field = None
        prices = event.get("prices", [])
        if len(prices) >= 3:
            price_cur = prices[0].get("currency", "$")
            old_value = prices[1].get("oldValue", 0)
            new_value = prices[2].get("newValue", 0)

            if new_value == 0:
                price_field = {"name": "Price", "value": "**Free!**", "inline": True}
            else:
                price_str = f"~~{price_cur}{old_value / 100:.2f}~~ → {price_cur}{new_value / 100:.2f}"
                price_field = {"name": "Price", "value": price_str, "inline": True}

        until = event.get("until") or event.get("end_date")
        if until and isinstance(until, int):
            until = datetime.datetime.fromtimestamp(until, tz=datetime.timezone.utc).strftime('%Y-%m-%d %H:%M UTC')

        # make the embed's fields
        fields = []
        if store:
            fields.append({"name": "Store", "value": store, "inline": True})
        if price_field:
            fields.append(price_field)
        if until:
            fields.append({"name": "Ends", "value": str(until), "inline": True})
        if event.get("rating") is not None:
            fields.append({"name": "Rating", "value": str(event["rating"]), "inline": True})
        if event.get("tags"):
            fields.append({"name": "Tags", "value": ", ".join(event["tags"]), "inline": False})
        if event.get("notice"):
            fields.append({"name": "Notice", "value": event["notice"], "inline": False})

        # make the embed woooo
        embed = base_embed(
            title=title,
            description=description,
            url=url,
            colour=hex_to_discord_color("#642d96"),
            thumbnail=image_url,
            fields=fields
        )

        await channel.send(embed=embed)

    async def cog_load(self):
        self._stop_event.clear()
        self._redis_task = asyncio.create_task(self.redis_listener())
        log.exception("RedisListener cog loaded and listening.")

    async def cog_unload(self):
        self._stop_event.set()
        if self._redis_task:
            self._redis_task.cancel()
            try:
                await self._redis_task
            except asyncio.CancelledError:
                pass
        log.exception("RedisListener cog unloaded and stopped.")

async def setup(bot):
    await bot.add_cog(RedisListener(bot))
