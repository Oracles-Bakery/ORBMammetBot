import discord
from discord.ext import commands
import pathlib
import logging
import settings
import asyncio
from utils.app.security import is_user_allowed
from utils.database import postgres

logger = logging.getLogger("bot")


# This gets the directory of the current file (admin.py) and appends admin_help to get the folder
ADMIN_HELP_DIR = pathlib.Path(__file__).parent / "admin_help"

"""
This badboy is setup in the __init__.py so that it can be loaded as a cog
These commands are NOT meant for regular users, but rather for the higher ups
That's why they aren't slash commands
"""

class Admin(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name='adminhelp')
    @is_user_allowed( "USER_ORACLE", "ROLE_GUILDMASTER", "BOT_OWNER")
    async def admin_help(self, ctx, command_name: str = None):
        """
        Show detailed admin help from admin_help/*.md files.
        Usage: ~adminhelp <command>
        """
        if command_name is None:
            # List all available admin help files
            files = [f.stem for f in ADMIN_HELP_DIR.glob('*.md')]
            text = "**Available admin help topics:**\n" + "\n".join(f"`{name}`" for name in files)
            await ctx.send(text)
            return

        helpfile = ADMIN_HELP_DIR / f"{command_name.lower()}.md"
        if helpfile.exists():
            with open(helpfile, 'r', encoding='utf-8') as f:
                await ctx.send(f.read())
        else:
            await ctx.send(f"No admin help found for `{command_name}`.")

    @commands.command(name="listmodules")
    @is_user_allowed( "USER_ORACLE", "ROLE_GUILDMASTER", "BOT_OWNER")
    async def list_modules(self, ctx: commands.Context):
        cogs = list(self.bot.cogs.keys())
        if not cogs:
            await ctx.send("No modules currently loaded.")
        else:
            await ctx.send(f"Loaded modules: {', '.join(cogs)}")

    @commands.command(name="loadallmodules")
    @is_user_allowed( "USER_ORACLE", "ROLE_GUILDMASTER", "BOT_OWNER")
    async def load_all_modules(self, ctx):
        base_dir = pathlib.Path(settings.COGS_DIR)
        loaded, failed = 0, []

        for pyfile in base_dir.rglob("*.py"):
            if pyfile.name.startswith("_"):
                continue
            rel_path = pyfile.relative_to(pathlib.Path().resolve())
            module = ".".join(rel_path.with_suffix("").parts)
            try:
                await self.bot.load_extension(module)
                loaded += 1
            except Exception as e:
                failed.append((module, str(e)))

        await ctx.send(f"Loaded {loaded} modules. Failed: {len(failed)}")
        if failed:
            await ctx.send("\n".join(f"• `{m}`: {e}" for m, e in failed[:16]))  # limit to 16 entries in case something super giga fucks up

    # Command only available to leadership role. For loading any unloaded cogs
    @commands.command(name="loadmodule")
    @is_user_allowed( "USER_ORACLE", "ROLE_GUILDMASTER", "BOT_OWNER")
    async def load_module(self, ctx, category: str, modname: str):
        module = f"cogs.{category}.{modname}"
        try:
            await self.bot.load_extension(module)
            await ctx.send(f"Loaded `{module}`.")
        except Exception as e:
            await ctx.send(f"Failed to load `{module}`: `{type(e).__name__}: {e}`")

    @commands.command(name="unloadmodule")
    @is_user_allowed( "USER_ORACLE", "ROLE_GUILDMASTER", "BOT_OWNER")
    async def unload_module(self, ctx, category: str, modname: str):
        module = f"cogs.{category}.{modname}"
        try:
            await self.bot.unload_extension(module)
            await ctx.send(f"Unloaded `{module}`.")
        except Exception as e:
            await ctx.send(f"Failed to unload `{module}`: `{type(e).__name__}: {e}`")

    @commands.command(name="reloadmodule")
    @is_user_allowed( "USER_ORACLE", "ROLE_GUILDMASTER", "BOT_OWNER")
    async def reload_module(self, ctx, category: str, modname: str):
        module = f"cogs.{category}.{modname}"
        try:
            await self.bot.reload_extension(module)
            await ctx.send(f"Reloaded `{module}`.")
        except Exception as e:
            await ctx.send(f"Failed to reload `{module}`: `{type(e).__name__}: {e}`")

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error: commands.CommandError):
        if isinstance(error, commands.CheckFailure):
            await ctx.send("You are not authorized to use this command.")
        else:
            logger.error(f"Unexpected error in admin command: {error}")
            await ctx.send(f"An unexpected error occurred: {type(error).__name__}: {error}")


    @commands.command(name="synccommands")
    @is_user_allowed( "USER_ORACLE", "ROLE_GUILDMASTER", "BOT_OWNER")
    async def sync_commands(self, ctx: commands.Context):
        try:
            guild_id = settings.GUILD_ID
            if not guild_id:
                await ctx.send("No guild ID set in settings.")
                return

            print("Loaded cogs:", self.bot.cogs)
            print("Registered app commands:", list(self.bot.tree.get_commands()))

            guild = discord.Object(id=guild_id)
            synced = await self.bot.tree.sync(guild=guild)
            await self.bot.tree.sync()
            await ctx.send(f"Synced {len(synced)} slash commands to the server.")
            logger.info("Slash commands manually synced to the server by %s", ctx.author)

        except Exception as e:
            logger.exception("Failed to sync slash commands.")
            await ctx.send(f"Failed to sync commands: `{type(e).__name__}: {e}`")

    @commands.command(name="listappcmds")
    async def list_app_commands(self, ctx):
        cmds = [f"{cmd.name}: {cmd}" for cmd in self.bot.tree.get_commands()]
        await ctx.send("App commands:\n" + "\n".join(cmds))

    @commands.command(name="nukecommands")
    @commands.is_owner()  # Only V can run this, and for good reason
    async def nuke_commands(self, ctx):
        """Remove all application commands from the current guild (careful!)."""
        guild = ctx.guild
        self.bot.tree.clear_commands(guild=guild)
        await self.bot.tree.sync(guild=guild)
        await ctx.send(f"Nuked all app commands for guild: {guild.id}")

    @commands.command(name="populatemembers")
    @is_user_allowed( "USER_ORACLE", "ROLE_GUILDMASTER", "BOT_OWNER")
    async def populatemembers(self, ctx):
        """Admin only: Populate the user DB with all current guild members."""
        await ctx.send("Starting to populate the members table... This may take a moment.")

        count, failed = 0, 0
        for member in ctx.guild.members:
            try:
                if member.bot:
                    continue # keeps the tincans from confusing later stuff
                # Use display_name if username is not enough
                preferred_name = member.nick if member.nick else member.name
                await postgres.execute("""
                    INSERT INTO user_data (
                        discord_id, join_date, discord_name, preferred_name, steam_id, created_at, edited_at
                    ) VALUES (
                        $1, $2, $3, $4, $5, NOW(), NOW()
                    ) ON CONFLICT (discord_id) DO NOTHING
                """,
                member.id,
                member.joined_at,
                member.name,
                preferred_name,
                None                  # steam_id populated by user choice later
                )
                count += 1
            except Exception as e:
                failed += 1
                # Log or print errors, but don't stop
                print(f"Failed to insert {member.id}: {e}")
            await asyncio.sleep(0.3)  # 300ms pause: ~3 inserts/sec, adjust if needed

        await ctx.send(f"Done. {count} members processed. {failed} failures.")


async def setup(bot: commands.Bot):
    await bot.add_cog(Admin(bot))
    logger.info("Admin module loaded.")