import discord
from discord import app_commands
from discord.ext import commands
from utils.colour import parse_colour_string
from datetime import datetime, timezone
from utils.database import postgres

# ───────────────────────────────────────────────────────────────
#   App Command: /setup_profile
#   Subcommands: NULL
# ───────────────────────────────────────────────────────────────

class ProfileSetup(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="setup_profile", description="Let the bot get to know you!")
    async def setup_profile(self, interaction: discord.Interaction):
        user = interaction.user

        try:
            dm_channel = await user.create_dm()
            await dm_channel.send("Hi there! Let's get the bot to know you. What do people usually call you?")

            def check_name(message):
                return message.author == user and message.channel == dm_channel

            name_msg = await self.bot.wait_for('message', check=check_name, timeout=120)
            preferred_name = name_msg.content.strip()

            await dm_channel.send(
                "Great! What's your favourite colour? (hex code like #00FFCC (no Alpha support I'm afraid), or a basic colour name like `red`, or CMYK like `0,100,100,0`)"
            )

            def check_color(message):
                return message.author == user and message.channel == dm_channel

            color_msg = await self.bot.wait_for('message', check=check_color, timeout=120)
            color_raw = color_msg.content.strip()

            encoded_colour = encode_colour(color_raw)
            colour = parse_colour_string(encoded_colour)

            join_date = user.joined_at.isoformat() if hasattr(user, "joined_at") and user.joined_at else datetime.now(timezone.utc)
            discord_name = user.name

            await postgres.execute(
                """
                INSERT INTO user_data (user_id, preferred_name, fav_colour, join_date, discord_name)
                VALUES ($1, $2, $3, $4, $5)
                ON CONFLICT (user_id) DO UPDATE SET
                    preferred_name = EXCLUDED.preferred_name,
                    fav_colour = EXCLUDED.fav_colour,
                    discord_name = EXCLUDED.discord_name
                """,
                user.id,
                preferred_name,
                encoded_colour,
                join_date,
                discord_name
            )

            embed = discord.Embed(
                title=f"Profile Set Up!",
                description=f"Name: {preferred_name}\nColor: {color_raw}",
                color=colour
            )
            await dm_channel.send(embed=embed)
            await interaction.response.send_message("Profile setup complete! Check your DMs.", ephemeral=True)
            # Easter egg: after sending everything else
            if color_raw.strip().lower() == "#00ffff" or color_raw.strip().lower() == "magenta":
                await dm_channel.send("Not a real colour but I forgive you.")


        except Exception as exc:
            await interaction.response.send_message("Could not DM you. Make sure your DMs are open!", ephemeral=True)

def encode_colour(input_str):
    s = input_str.strip()
    if s.startswith("#") and len(s) == 7:
        return f"hex|{s[1:]}"
    elif "," in s and all(x.strip().isdigit() for x in s.split(",")):
        return f"cmyk|{s}"
    else:
        return f"name|{s.lower()}"

async def setup(bot: commands.Bot):
    await bot.add_cog(ProfileSetup(bot))
