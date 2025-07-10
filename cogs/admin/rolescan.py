from discord.ext import commands
import discord
import utils.database.postgres as postgres
from utils.app.security import is_user_allowed
import logging

logger = logging.getLogger("bot")

class RoleScanner(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="scanroles")
    @is_user_allowed( "USER_ORACLE", "ROLE_GUILDMASTER", "USER_BOT_OWNER")
    async def scan_roles(self, ctx):
        """Scans all roles in the guild and upserts them into the database."""
        guild: discord.Guild = ctx.guild

        if guild is None:
            await ctx.send("This command must be run in a guild.")
            return

        roles = guild.roles
        if not roles:
            await ctx.send("This guild has no roles to scan.")
            return
        successful = 0
        skipped = 0

        for role in roles:
            # Skip @everyone and managed roles (e.g., integration/webhook roles)
            if role.is_default() or role.managed or role.name.strip().startswith("↳"):
                skipped += 1
                logger.debug(f"Skipped role {role.id} - {role.name} (managed or @everyone)")
                continue

            try:
                await postgres.upsert_role(
                    role_id=role.id,
                    role_name=role.name
                )
                successful += 1
            except Exception as e:
                logger.exception(f"Failed to upsert role {role.id} - {role.name}: {e}")
                await ctx.send(f"Error storing role: {role.name}")
                continue

        await ctx.send(
            f"Scanned roles in **{guild.name}**.\n"
            f"**{successful}** stored or updated in the database.\n"
            f"**{skipped}** skipped (e.g., managed roles or `@everyone`)."
        )

async def setup(bot):
    await bot.add_cog(RoleScanner(bot))
