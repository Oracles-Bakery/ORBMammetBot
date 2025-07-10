"""
This is the main file of the bot and should be the one we're running to start it up.
"""

import asyncio
import discord
import settings
import utils.database.postgres as postgres
import utils.community.roleselection as roleselection
import os
import pathlib
from discord.ext import commands
from utils.app.status import write_status

logger = settings.logging.getLogger("bot")

# List of cogs that should always be loaded and protected from unload/reload
ESSENTIAL_COGS = ["cogs.admin"]

import pathlib

async def bootstrap_schema(conn, sql_path="buildAll.sql"):
    sql_file = pathlib.Path(sql_path)
    if not sql_file.exists():
        raise FileNotFoundError(f"SQL schema file not found: {sql_path}")

    with open(sql_file, "r") as f:
        schema_sql = f.read()

    # asyncpg has to do each statement individually so split at ';'
    statements = [stmt.strip() for stmt in schema_sql.split(";") if stmt.strip()]
    for stmt in statements:
        await conn.execute(stmt)


async def heartbeat_task():
    """
    Periodically writes an "online" status to a status file every 5 minutes.

    This acts as a heartbeat signal to indicate the bot is alive.
    The status is written immediately on startup and then every 300 seconds.
    """
    await write_status("online", reason="Bot just started")

    while True:
        await write_status("online")
        await asyncio.sleep(300)  # every 5 minutes

def walk_cogs(cogs_dir, essential_cogs=None):
    """
    Recursively walks the cogs/ directory and returns all Python module paths
    that can be used with bot.load_extension.
    Skips files/folders named 'experimental', and loads __init__.py only for essential cogs.
    """
    paths = []
    cogs_dir = pathlib.Path(cogs_dir)  # ensure it's a Path
    essential_cogs = set(essential_cogs or [])

    for root, dirs, files in os.walk(cogs_dir):
        # Skip 'experimental' folders by name
        if 'experimental' in pathlib.Path(root).parts:
            continue
        for file in files:
            file_path = pathlib.Path(root) / file
            if 'experimental' in file_path.parts:
                continue  # skip any file in an experimental subfolder
        root_path = pathlib.Path(root)
        for file in files:
            if file == "__init__.py":
                module_rel_path = root_path.relative_to(cogs_dir)
                module_path = f"cogs.{module_rel_path.as_posix().replace('/', '.')}"
                if module_path in essential_cogs:
                    paths.append(module_path)
            elif file.endswith(".py") and not file.startswith("__"):
                module_rel_path = root_path.relative_to(cogs_dir)
                if module_rel_path.parts:
                    module_path = f"cogs.{module_rel_path.as_posix().replace('/', '.')}.{file[:-3]}"
                else:
                    module_path = f"cogs.{file[:-3]}"
                paths.append(module_path)
    return paths


async def restore_persistent_views(bot):
    """
    Restores all persistent views on startup using the consistentChannels table.
    """
    try:
        # Pull all tracked channel/message/purpose rows
        entries = await postgres.fetch_all_consistent_channels()
        if not entries:
            logger.info("No persistent views to restore.")
            return
        for entry in entries:
            purpose = entry["purpose"]
            channel_id = entry["channel_id"]
            message_id = entry["message_id"]

            guild = bot.get_guild(settings.GUILD_ID)  # You may want to generalize for multi-guild
            if not guild:
                logger.warning(f"Guild {settings.GUILD_ID} not found for persistent view {purpose}")
                continue

            channel = guild.get_channel(channel_id)
            if not channel:
                logger.warning(f"Channel {channel_id} not found for {purpose}")
                continue

            try:
                msg = await channel.fetch_message(message_id)
            except Exception as e:
                logger.warning(f"Failed to fetch message {message_id} in channel {channel_id}: {e}")
                continue

            # You can add more views by purpose here
            if purpose == "roleselection":
                view = roleselection.RoleCategoryView(bot)
            else:
                logger.info(f"No view restoration handler for {purpose}, skipping")
                continue

            try:
                await msg.edit(view=view)
                logger.info(f"Restored persistent view '{purpose}' in channel {channel.name}")
            except Exception as e:
                logger.warning(f"Failed to edit message for {purpose}: {e}")

    except Exception as exc:
        logger.exception(f"Error during persistent view restoration: {exc}")



async def run():
    intents = discord.Intents.all()
    bot = commands.Bot(command_prefix="~", intents=intents)

    @bot.event
    async def on_ready():
        """
        Event handler triggered when the bot is connected and ready.
        - Starts the heartbeat task if not already started
        - Loads dev-only extensions and syncs slash commands if in dev environment
        - Logs bot readiness info
        """
        if not hasattr(bot, "heartbeat_started"):
            bot.loop.create_task(heartbeat_task())
            bot.heartbeat_started = True # type: ignore     like it's literally an if not come on

        logger.info("Ready reported as %s with UID %s", bot.user, bot.user.id) # type: ignore
        logger.info("Loaded %s commands in %s cogs", len(bot.commands), len(bot.cogs))

        await restore_persistent_views(bot)

    # error handling for commands
    @bot.event
    async def on_command_error(ctx, error):
        """
        Global error handler for commands.

        - Logs the error for debugging and informs the user that something is wrong
        """
        logger.warning("Command error in '%s': %r", getattr(ctx.command, 'qualified_name', 'unknown'), error)

        if isinstance(error, commands.CommandNotFound):
            await ctx.send("Command not found.")
            return

        if isinstance(error, commands.MissingRequiredArgument):
            logger.warning("Command error in '%s': %r", getattr(ctx.command, 'qualified_name', 'unknown'), error)
            await ctx.send("You're missing a required argument.")
            return

        if isinstance(error, commands.BadArgument):
            logger.warning("Command error in '%s': %r", getattr(ctx.command, 'qualified_name', 'unknown'), error)
            await ctx.send("One or more arguments were invalid.")
            return

        if isinstance(error, commands.MissingPermissions):
            logger.warning("Command error in '%s': %r", getattr(ctx.command, 'qualified_name', 'unknown'), error)
            await ctx.send("You lack the necessary Discord permissions for this command.")
            return

        if isinstance(error, commands.BotMissingPermissions):
            logger.warning("Command error in '%s': %r", getattr(ctx.command, 'qualified_name', 'unknown'), error)
            await ctx.send("I lack the necessary Discord permissions for that!")
            return

        if isinstance(error, commands.CommandOnCooldown):
            logger.warning("Command error in '%s': %r", getattr(ctx.command, 'qualified_name', 'unknown'), error)
            await ctx.send(f"That command is on cooldown. Try again in {round(error.retry_after, 1)}s.")
            return

        if isinstance(error, commands.CheckFailure):
            logger.warning("Command error in '%s': %r", getattr(ctx.command, 'qualified_name', 'unknown'), error)
            await ctx.send("You do not have permission to use this command.")
            return

        if isinstance(error, commands.NoPrivateMessage):
            logger.warning("Command error in '%s': %r", getattr(ctx.command, 'qualified_name', 'unknown'), error)
            await ctx.send("This command can only be used in a server, not in DMs.")
            return

        if isinstance(error, commands.DisabledCommand):
            logger.warning("Command error in '%s': %r", getattr(ctx.command, 'qualified_name', 'unknown'), error)
            await ctx.send("That command is currently disabled.")
            return

        if isinstance(error, commands.TooManyArguments):
            logger.warning("Command error in '%s': %r", getattr(ctx.command, 'qualified_name', 'unknown'), error)
            await ctx.send("You provided too many arguments to the command.")
            return

        if isinstance(error, commands.CommandInvokeError):
            logger.warning("Command error in '%s': %r", getattr(ctx.command, 'qualified_name', 'unknown'), error)
            await ctx.send(f"An internal error occurred: {type(error.original).__name__}: {error.original}")
            return

        # Unhandled errors
        logger.error("Unhandled command error: %s", error)
        raise error

    # Database connection
    try:
        await postgres.connect()
        logger.info("Database connection pool created")
    except Exception:
        logger.exception("Failed to connect to the database")
        return

    # Load cogs recursively
    loaded_cogs = set()
    for cog_module in walk_cogs(settings.COGS_DIR):
        print(f"Auto-loading extension: {cog_module}")
        if cog_module not in loaded_cogs:
            try:
                await bot.load_extension(cog_module)
                logger.info(f"Loaded extension: {cog_module}")
                loaded_cogs.add(cog_module)
            except Exception as e:
                print(f"Failed to auto-load extension: {cog_module} ({type(e).__name__}: {e})")
                logger.exception("Failed to load cog: %s", cog_module)

    # Ensure essential cogs are loaded (in case walk_cogs misses them)
    for essential in ESSENTIAL_COGS:
        if essential not in loaded_cogs:
            try:
                await bot.load_extension(essential)
                logger.info(f"Loaded essential extension: {essential}")
            except Exception:
                logger.exception("Failed to load essential cog: %s", essential)

    # Start the bot
    try:
        await bot.start(settings.TOKEN) # type: ignore
    except asyncio.CancelledError:
        logger.warning("Bot shutdown was requested")
    finally:
        # Write offline status on shutdown
        await write_status("offline", reason="Bot shutdown")
        await bot.close()
        await postgres.close()
        logger.info("Database connection pool closed")
        logger.info("Bot has been shut down safely")


if __name__ == "__main__":
    asyncio.run(run())
