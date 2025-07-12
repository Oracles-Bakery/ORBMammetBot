import discord
import settings

from discord.ext import commands
from utils.database import postgres
from utils.app.security import is_user_allowed


logger = settings.logging.getLogger("bot")

class DatabaseDiag(commands.Cog):
    """Database health check commands."""

    # Test if the database connection is working
    @commands.command(name="testdbconnection", help="Tests the database connection")
    @is_user_allowed( "USER_ORACLE", "ROLE_GUILDMASTER", "USER_BOT_OWNER")
    async def test_db_connection(self, ctx: commands.Context):
        try:
            await ctx.send("Attempting to connect to database...")

            result = await postgres.fetchval("SELECT 1;")
            if result == 1:
                await ctx.send("Database connection successful.")
            else:
                await ctx.send("Database connection test returned unexpected result.")
        except Exception as e:
            logger.exception("Database connection test failed.")
            await ctx.send(f"Error during DB test: `{type(e).__name__}: {e}`")

    # Find the number of rows in a table
    @commands.command(name="dbrowcount", help="Gets the number of rows in a table")
    @is_user_allowed( "USER_ORACLE", "ROLE_GUILDMASTER", "USER_BOT_OWNER")
    async def db_row_count(self, ctx: commands.Context, tablename: str):
        try:
            await ctx.send("Attempting to connect to database...")

            tablename=tablename.lower()
            result = await postgres.fetchval(f"SELECT COUNT(*) FROM {tablename};")
            await ctx.send(f"Number of rows in table `{tablename}`: {result}")
        except Exception as e:
            logger.exception("Database row count test failed.")
            await ctx.send(f"Error during DB row count test: `{type(e).__name__}: {e}`")

    # List all role categories and their counts
    @commands.command(name="dbrolecategories", help="Lists all role categories and their counts")
    @is_user_allowed( "USER_ORACLE", "ROLE_GUILDMASTER", "USER_BOT_OWNER")
    async def db_role_categories(self, ctx: commands.Context):
        try:
            rows = await postgres.fetch("""
                SELECT category, COUNT(*) as count
                FROM discord_roles
                GROUP BY category
                ORDER BY category;
            """)
            if not rows:
                await ctx.send("No roles found in the database.")
                return

            lines = ["**Role Categories in Database:**"]
            for row in rows:
                category = row['category'] or "Uncategorized"
                lines.append(f"• {category} — {row['count']} roles")

            await ctx.send("\n".join(lines))
        except Exception as e:
            logger.exception("Failed to retrieve role category counts")
            await ctx.send(f"Error checking role categories: `{type(e).__name__}: {e}`")


    # Check the most recent entries in a table, defaults to 5
    @commands.command(name="dbrecent", help="Checks the most recent **n** (default 5) created or edited rows in a table")
    @is_user_allowed( "USER_ORACLE", "ROLE_GUILDMASTER", "USER_BOT_OWNER")
    async def db_recent(self, ctx: commands.Context, tablename: str, limit: int = 5):
        try:
            await ctx.send("Attempting to connect to database...")

            rows = await postgres.fetch(f"SELECT * FROM {tablename} ORDER BY edited_at DESC LIMIT {limit};")
            if not rows:
                await ctx.send(f"No recent rows found in table `{tablename}`.")
                return

            lines = [f"**Most Recent {limit} Rows in `{tablename}`:**"]
            for row in rows:
                lines.append(f"• {row}")

            await ctx.send("\n".join(lines))
        except Exception as e:
            logger.exception("Failed to retrieve recent rows")
            await ctx.send(f"Error checking recent rows: `{type(e).__name__}: {e}`")

    # Check database integrity for NULLs in required fields and invalid foreign keys
    @commands.command(name="checkdbintegrity", help="Checks for NULLs in required fields and invalid foreign keys")
    @is_user_allowed("USER_ORACLE", "ROLE_GUILDMASTER", "USER_BOT_OWNER")
    async def check_db_integrity(self, ctx: commands.Context):
        try:
            issues = []

            # Check for NULL required fields in user_data
            rows = await postgres.fetch(
                "SELECT * FROM user_data WHERE discord_id IS NULL OR discord_name IS NULL OR preferred_name IS NULL"
            )
            if rows:
                issues.append(f"`user_data`: {len(rows)} row(s) have NULLs in required fields.")

            # Check user_warnings has valid user_data links
            rows = await postgres.fetch("""
                SELECT uw.user_warned FROM user_warnings uw
                LEFT JOIN user_data u ON u.discord_id = uw.user_warned
                WHERE u.discord_id IS NULL
            """)
            if rows:
                issues.append(f"`user_warnings`: {len(rows)} row(s) reference nonexistent users in user_data.")

            # Check xiv_char has valid user_data links
            rows = await postgres.fetch("""
                SELECT c.discord_id FROM xiv_char c
                LEFT JOIN user_data u ON u.discord_id = c.discord_id
                WHERE c.discord_id IS NOT NULL AND u.discord_id IS NULL
            """)
            if rows:
                issues.append(f"`xiv_char`: {len(rows)} row(s) reference missing users in user_data.")

            # Check for NULLs in critical fields in xiv_jobs
            rows = await postgres.fetch("""
                SELECT * FROM xiv_jobs 
                WHERE job_name IS NULL OR full_name IS NULL OR job_role IS NULL OR category IS NULL
            """)
            if rows:
                issues.append(f"`xiv_jobs`: {len(rows)} row(s) have NULLs in critical job fields.")

            # Validate consistentChannels references
            bad_channels = []
            bad_messages = []
            for row in await postgres.fetch("SELECT * FROM consistentChannels"):
                channel_id = row["channel_id"]
                message_id = row["message_id"]
                channel = ctx.guild.get_channel(channel_id)
                if channel is None:
                    bad_channels.append(channel_id)
                    continue
                if message_id is not None:
                    try:
                        await channel.fetch_message(message_id)
                    except discord.NotFound:
                        bad_messages.append((channel_id, message_id))
                    except discord.Forbidden:
                        issues.append(f"Missing permissions for channel `{channel_id}`.")
                    except Exception as e:
                        issues.append(f"Unexpected error checking message `{message_id}` in channel `{channel_id}`: {e}")
            if bad_channels:
                issues.append(f"`consistentChannels`: {len(bad_channels)} missing channel(s): {bad_channels}")
            if bad_messages:
                formatted = ", ".join(f"{cid}/{mid}" for cid, mid in bad_messages)
                issues.append(f"`consistentChannels`: {len(bad_messages)} message(s) not found: {formatted}")

            # Output information
            if issues:
                await ctx.send("Database integrity issues found:\n" + "\n".join(issues))
            else:
                await ctx.send("Database integrity check passed — no issues found.")

        except Exception as e:
            logger.exception("Database integrity check failed.")
            await ctx.send(f"Error during DB test: `{type(e).__name__}: {e}`")

    @commands.command(name="checkdbhealth", help="Checks DB schema against buildAll.sql for missing tables/columns")
    @is_user_allowed("USER_ORACLE", "ROLE_GUILDMASTER", "USER_BOT_OWNER")
    async def check_db_health(self, ctx: commands.Context):
        try:
            await ctx.send("Checking database schema against buildAll.sql...")
            sql_path = Path("utils/buildAll.sql")  # UPDATE if your path differs
            if not sql_path.exists():
                await ctx.send(f"Could not find SQL file at {sql_path}.")
                return
            sql_text = sql_path.read_text()
            expected_schema = postgres.parse_sql_schema(sql_text)
            actual_schema = await postgres.get_actual_schema()
            issues = postgres.compare_schemas(expected_schema, actual_schema)
            if issues:
                await ctx.send("**DB health check found issues:**\n" + "\n".join(issues))
            else:
                await ctx.send("**DB health check passed:** All tables and columns present!")
        except Exception as e:
            logger.exception("Database health check failed.")
            await ctx.send(f"Error during DB health check: `{type(e).__name__}: {e}`")


    # Error handler for classic commands
    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error: commands.CommandError):
        if isinstance(error, commands.CheckFailure):
            await ctx.send("You are not authorized to use this command.")
        else:
            logger.error(f"Unexpected error in admin command: {error}")

async def setup(bot: commands.Bot):
    await bot.add_cog(DatabaseDiag(bot))