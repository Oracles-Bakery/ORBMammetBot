from discord.ext import commands
import settings
import logging
from utils.app.security import is_user_allowed
from utils.app.status import write_status

logger = logging.getLogger("bot")

class ShutdownCommand(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="shutdown", help="Gracefully shuts down the bot")
    @is_user_allowed("USER_GUILDMASTER", "USER_ORACLE", "USER_BOT_OWNER")
    async def shutdown(self, ctx: commands.Context, inform_admin: bool = False, *, description: str = ""):
        await ctx.send("Shutting down...")

        logger.info("Shutdown initiated by %s", ctx.author)

        shutdown_reason = f"Shutdown by {ctx.author}."
        if description:
            shutdown_reason += f" Reason: {description}"

        await write_status("offline", reason=shutdown_reason)

        if inform_admin:
            try:
                admin_user = await self.bot.fetch_user(settings.USER_BOT_OWNER)
                dm_message = (
                    f"Bot shutdown initiated by {ctx.author}.\n"
                    f"Description: {description or 'No description provided.'}"
                )
                await admin_user.send(dm_message)
            except Exception as e:
                logger.error(f"Failed to DM admin on shutdown: {e}")

        await self.bot.close()

async def setup(bot: commands.Bot):
    await bot.add_cog(ShutdownCommand(bot))
    logger.info("Shutdown command loaded.")
