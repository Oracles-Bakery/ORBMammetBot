import discord
from discord.ext import commands

import utils.database.postgres as postgres
import utils.community.roleselection as roleselection
from utils.app.security import is_user_allowed
import settings

logger = settings.logging.getLogger("bot")

class RoleSetupCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="setuproles")
    @is_user_allowed( "USER_ORACLE", "ROLE_GUILDMASTER", "USER_BOT_OWNER")
    async def setup_roles(self, ctx):
        """Set up the role selection message in the roleselection channel"""
        
        channel_id = settings.CHANNEL_ROLESELECTION  # This is your integer channel ID
        # Fetch the channel object from the current guild
        channel = ctx.guild.get_channel(channel_id)
        if channel is None:
            await ctx.send(f"Could not find a channel with ID `{channel_id}` in this server.")
            return

        # Step 1: Check if DB already has a registered role selection message
        existing_entry = await postgres.get_consistent_channel_by_purpose(purpose="roleselection")
        if existing_entry:
            try:
                # Attempt to fetch the actual message
                existing_channel = ctx.guild.get_channel(existing_entry["channel_id"])
                if existing_channel is None:
                    raise ValueError("Channel no longer exists")

                msg = await existing_channel.fetch_message(existing_entry["message_id"])
                # Alert to broken message structure
                if not msg.embeds or not msg.components:
                    raise ValueError("Old message found but it doesn't match expected format.")
                # If successful, exit early
                await ctx.send(
                    f"A role selection message already exists in {existing_channel.mention}.\n"
                    f"If you want to replace it, manually delete the old one or clear the DB entry."
                )
                return

            except discord.NotFound:
                # Message is gone — continue to recreate
                await ctx.send("Old role selection message was deleted. A new one will be created.")
            except Exception as e:
                await ctx.send(f"Failed to verify existing role selection message: {e}")
                return

        # Step 2: Create and send new message
        embed = discord.Embed(
            title="Role assignment",
            description=(
                "Choose your preferences by clicking a category button below.\n"
                "Each category will open a menu for you to select the roles that apply to you."
            ),
            color=discord.Color.blurple()
        )
        view = roleselection.RoleCategoryView(self.bot)

        try:
            message = await channel.send(embed=embed, view=view)
        except discord.Forbidden:
            await ctx.send("I don't have permission to send messages in that channel.")
            return
        except Exception as e:
            await ctx.send(f"Failed to send role selector message: {e}")
            return

        # Step 3: Store or update DB entry
        try:
            await postgres.upsert_consistent_channel(
                purpose="roleselection",
                channel_id=channel.id,
                message_id=message.id
            )
        except Exception as e:
            await ctx.send(f"Failed to save role selection message info to database: {e}")
            return

        await ctx.send(f"Role selection message sent to {channel.mention} and registered in the database.")


async def setup(bot):
    await bot.add_cog(RoleSetupCommand(bot))
    logger.info("Role picker setup command loaded.")
