import discord
from discord import app_commands
from discord.ext import commands
import asyncio
import base64
import secrets
import settings

from utils.database import postgres, redis
from utils.lodestone_scraper.scraper import LodestoneScraper

logger = settings.logging.getLogger("bot")


async def fetch_bio(lodestone_id, region="na"):
    scraper = LodestoneScraper(region=region)
    # The selector string is for the About Me field, adjust as needed:
    data = await scraper.scrape("profile.character.BIO", lodestone_id)
    return data or ""

async def fetch_basic_profile(lodestone_id, region="na"):
    scraper = LodestoneScraper(region=region)
    # You can fetch all these at once if your selectors.json supports it:
    data = await scraper.scrape("profile.character", lodestone_id)
    return {
        "forename": data.get("NAME", "").split(" ")[0] if data.get("NAME") else "",
        "surname": data.get("NAME", "").split(" ")[1] if data.get("NAME") and len(data.get("NAME").split(" ")) > 1 else "",
        "server_name": data.get("SERVER", {}).get("World") if isinstance(data.get("SERVER"), dict) else "",
        "data_center_name": data.get("SERVER", {}).get("DC") if isinstance(data.get("SERVER"), dict) else "",
    }


# ───────────────────────────────────────────────────────────────
#   App Command Group: /whoami
#   Subcommands: /whoami create, /whoami view
# ───────────────────────────────────────────────────────────────

class WhoAmIGroup(app_commands.Group):
    def __init__(self):
        super().__init__(name="whoami", description="Manage your linked FFXIV character")

    # Gets the command working on linking your lodestone profile
    @app_commands.command(name="create", description="Link your FFXIV character")
    async def create(self, interaction: discord.Interaction):
        token_b64 = base64.b64encode(secrets.token_bytes(16)).decode("utf-8")
        await redis.set_verification(interaction.user.id, token_b64, ttl=600)
        file = discord.File("static/img/lodestonecharprofguide.png", filename="lodestonecharprofguide.png")
        embed = discord.Embed(
            title="Verify Your Character",
            colour=discord.Colour.green(),
            description = (
                "Add the following code to your Lodestone profile's **Character profile** field:\n\n"
                f"```\n\n{token_b64}\n\n```\n"
                "After saving it on the Lodestone site, press **Verify** and give me your Lodestone ID."
            ),
        )

        embed.set_image(url="attachment://lodestonecharprofguide.png")
        await interaction.response.send_message(
            embed=embed,
            file=file,
            view=VerifyButtonView(token_b64),
            ephemeral=True,
        )

    # And this displays it (very limited right now)
    @app_commands.command(name="view", description="Show your linked FFXIV character")
    async def view(self, interaction: discord.Interaction):
        row = await postgres.fetchrow(
            "SELECT * FROM xiv_char WHERE discord_id = $1",
            interaction.user.id,
        )

        if row:
            embed = discord.Embed(
                title="Linked Character",
                colour=discord.Colour.blurple(),
            )
            embed.add_field(
                name="Name",
                value=f"{row['forename']} {row['surname']}",
                inline=False,
            )
            embed.add_field(name="Server", value=row["server_name"], inline=True)
            embed.add_field(name="Data Center", value=row["data_center_name"], inline=True)
            await interaction.response.send_message(embed=embed, ephemeral=False)
        else:
            await interaction.response.send_message(
                "You haven't linked a character yet. Use `/whoami create` to get started.",
                ephemeral=True,
            )


class WhoAmI(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.bot.tree.add_command(WhoAmIGroup())
        print("App commands now:", list(self.bot.tree.get_commands()))



# pls don't touch this I'm pretty sure there's a load-bearing coconut.jpg in here
class VerifyButtonView(discord.ui.View):
    def __init__(self, token: str):
        super().__init__(timeout=600)
        self.token = token

    @discord.ui.button(label="Verify", style=discord.ButtonStyle.green)
    async def verify_button(self, interaction: discord.Interaction, _: discord.ui.Button):
        await interaction.response.send_modal(VerifyModal(self.token))

class VerifyModal(discord.ui.Modal, title="Lodestone Verification"):
    lodestone_id: discord.ui.TextInput = discord.ui.TextInput(
        label="Lodestone ID", placeholder="e.g. 12345678"
    )

    def __init__(self, token: str):
        super().__init__()
        self.token = token

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        user_id = interaction.user.id
        lodestone_id_raw = self.lodestone_id.value.strip()
        pending_token = await redis.get_verification(user_id)
        if pending_token is None or pending_token != self.token:
            await interaction.followup.send(
                "Verification token expired or invalid.", ephemeral=True
            )
            return
        try:
            bio_text = await fetch_bio(lodestone_id_raw)
            if self.token not in bio_text:
                await interaction.followup.send(
                    "Token not found in the profile. Make sure you pasted it in **Character Profile** "
                    "and that the Lodestone page has finished saving.",
                    ephemeral=True,
                )
                return
            parsed = await fetch_basic_profile(lodestone_id_raw)
            logger = settings.logging.getLogger("whoami_debug")
            logger.info("DEBUG parsed: %r", parsed)
            logger.info("DEBUG insert args: %r", [
                int(lodestone_id_raw),
                user_id,
                parsed.get("forename", ""),
                parsed.get("surname", ""),
                parsed.get("server_name", ""),
                parsed.get("data_center_name", ""),
            ])
            await postgres.execute(
                """
                INSERT INTO xiv_char
                    (lodestone_id, discord_id, forename, surname, server_name, data_center_name)
                VALUES
                    ($1, $2, $3, $4, $5, $6)
                ON CONFLICT (lodestone_id) DO UPDATE
                    SET discord_id = EXCLUDED.discord_id
                """,
                int(lodestone_id_raw),
                user_id,
                parsed.get("forename", ""),
                parsed.get("surname", ""),
                parsed.get("server_name", ""),
                parsed.get("data_center_name", ""),
            )
            await redis.delete_verification(user_id)
            await interaction.followup.send(
                "Character verified and linked!", ephemeral=True
            )
        except Exception as exc:
            logger.error("Exception during verification", exc_info=True)
            await interaction.followup.send(
                f"Error during verification: {type(exc).__name__}: {exc}",
                ephemeral=True,
            )


async def setup(bot: commands.Bot):
    await bot.add_cog(WhoAmI(bot))
