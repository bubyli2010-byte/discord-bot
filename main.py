import discord
from discord.ext import commands
from discord import app_commands
import os

TOKEN = os.getenv("TOKEN")

EMBED_COLOR_OPEN   = 0xFF0000
EMBED_COLOR_CLOSED = 0x808080

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

rp_status = {"open": False, "code": None}

@tree.command(name="rpstatus", description="Setzt den RP-Status und den Code")
@app_commands.describe(
    status="RP geöffnet oder geschlossen?",
    code="Der RP-Code (nur bei geöffnetem RP nötig)",
    ping="Rolle oder User pingen?"
)
@app_commands.choices(status=[
    app_commands.Choice(name="RP ist geöffnet", value="open"),
    app_commands.Choice(name="RP ist geschlossen", value="closed"),
])
async def rpstatus(
    interaction: discord.Interaction,
    status: app_commands.Choice[str],
    code: str = None,
    ping: str = None
):
    is_open = status.value == "open"
    rp_status["open"] = is_open
    rp_status["code"] = code if is_open else None

    if is_open:
        embed = discord.Embed(
            title="Das RP ist jetzt geöffnet!",
            description=(
                "Wir freuen uns, dass du dabei bist!\n"
                "Viel Spaß beim Roleplay und bleib immer im Charakter.\n"
                "Beachte bitte die Regeln und respektiere alle Mitspieler.\n"
                "Wir wünschen dir eine tolle Zeit!"
            ),
            color=EMBED_COLOR_OPEN
        )
        embed.add_field(name="Status", value="Geöffnet", inline=True)
        if code:
            embed.add_field(name="Code", value=f"```{code}```", inline=False)
    else:
        embed = discord.Embed(
            title="Das RP ist jetzt geschlossen.",
            description=(
                "Das Roleplay wurde beendet.\n"
                "Wir hoffen, du hattest eine gute Zeit!\n"
                "Bis zum nächsten Mal."
            ),
            color=EMBED_COLOR_CLOSED
        )
        embed.add_field(name="Status", value="Geschlossen", inline=True)

    ping_text = ping if ping else ""

    await interaction.response.send_message(
        content=ping_text,
        embed=embed
    )

    await interaction.followup.send(
        "Status wurde erfolgreich gesetzt!",
        ephemeral=True
    )

@bot.event
async def on_ready():
    await tree.sync()
    print(f"Bot ist online als {bot.user} - Slash-Commands synchronisiert!")

bot.run(TOKEN)
