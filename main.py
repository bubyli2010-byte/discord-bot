import discord
from discord.ext import commands
from discord import app_commands
import os

# Konfiguration
TOKEN = os.getenv("TOKEN")

EMBED_COLOR_OPEN   = 0xFF0000
EMBED_COLOR_CLOSED = 0x808080

# Bot Setup
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

# Globaler RP-Status
rp_status = {"open": False, "code": None}

# /rpstatus Command
@tree.command(name="rpstatus", description="Setzt den RP-Status und den Code")
@app_commands.describe(
    status="RP geoeffnet oder geschlossen?",
    code="Der RP-Code (nur bei geoeffnetem RP noetig)",
    ping="Rolle oder User pingen?"
)
@app_commands.choices(status=[
    app_commands.Choice(name="RP ist geoeffnet", value="open"),
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

    color = EMBED_COLOR_OPEN if is_open else EMBED_COLOR_CLOSED
    status_text = "**Geoeffnet**" if is_open else "**Geschlossen**"

    embed = discord.Embed(title="RP-Status", color=color)
    embed.add_field(name="Status", value=status_text, inline=False)

    if is_open and code:
        embed.add_field(name="Code", value=f"```{code}```", inline=False)

    if ping:
        embed.add_field(name="Ping", value=ping, inline=False)

    embed.set_footer(text=f"Gesetzt von {interaction.user.display_name}")

    ping_text = ping if ping else ""
    await interaction.response.send_message(content=ping_text, embed=embed)

# Bot Ready
@bot.event
async def on_ready():
    await tree.sync()
    print(f"Bot ist online als {bot.user} - Slash-Commands synchronisiert!")

# Starten
bot.run(TOKEN)
