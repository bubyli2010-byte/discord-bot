# main.py
import discord
from discord import app_commands
from discord.ext import commands
import os

# ────────────────────────────────────────────────
# KONFIGURATION
# ────────────────────────────────────────────────

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(
    command_prefix="!",
    intents=intents,
    help_command=None
)

# Globale Variable (könnte später in DB / JSON gespeichert werden)
RP_STATUS = {"open": False}  # Standard: geschlossen

# ─── Persistent View mit Select Menu ────────────────────────────────

class RPStatusView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)  # persistent

    @discord.ui.select(
        custom_id="rp_status_select",
        placeholder="RP Status ändern...",
        min_values=1,
        max_values=1,
        options=[
            discord.SelectOption(label="Geöffnet", value="open", emoji="✅"),
            discord.SelectOption(label="Geschlossen", value="closed", emoji="❌"),
        ]
    )
    async def status_select(self, interaction: discord.Interaction, select: discord.ui.Select):
        new_value = select.values[0] == "open"
        RP_STATUS["open"] = new_value

        embed = discord.Embed(
            title="RP-Status aktualisiert",
            description=f"RP ist jetzt **{'geöffnet' if new_value else 'geschlossen'}**.",
            color=discord.Color.green() if new_value else discord.Color.red(),
            timestamp=discord.utils.utcnow()
        )
        embed.set_footer(text=f"Geändert von {interaction.user}")

        await interaction.response.edit_message(embed=embed, view=self)


# ─── Bot Events ─────────────────────────────────────────────────────

@bot.event
async def on_ready():
    print(f"Eingeloggt als {bot.user}")
    # Persistent View registrieren (wichtig für Select nach Restart)
    bot.add_view(RPStatusView())


# ─── Slash Commands ─────────────────────────────────────────────────

@bot.tree.command(name="rpstatus", description="Zeigt den aktuellen RP-Status + Umschalt-Menü")
@app_commands.default_permissions(manage_guild=True)  # nur Admins/Moderatoren
async def rpstatus(interaction: discord.Interaction):
    embed = discord.Embed(
        title="RP-Status",
        description=f"**Aktueller Status:** {'Geöffnet' if RP_STATUS['open'] else 'Geschlossen'}",
        color=discord.Color.green() if RP_STATUS['open'] else discord.Color.red(),
        timestamp=discord.utils.utcnow()
    )
    embed.set_footer(text="Ändere den Status mit dem Dropdown-Menü unten")

    view = RPStatusView()
    await interaction.response.send_message(embed=embed, view=view)


@bot.tree.command(name="code", description="Code posten – nur wenn RP geöffnet ist")
@app_commands.describe(
    code="Dein RP-Code / Invite-Link / etc.",
    ping="Wen soll der Bot pingen? (User / Rolle / everyone)"
)
async def post_code(interaction: discord.Interaction, code: str, ping: str = None):
    if not RP_STATUS["open"]:
        embed = discord.Embed(
            title="RP ist geschlossen",
            description="Momentan können keine Codes gepostet werden.\nWarte bis jemand den Status auf **Geöffnet** setzt.",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    # Embed für den Channel
    embed = discord.Embed(
        title="Neuer RP-Code verfügbar!",
        description=f"**Code:** ```{code}```",
        color=discord.Color.blue(),
        timestamp=discord.utils.utcnow()
    )
    embed.set_footer(text=f"von {interaction.user}")

    content = ping if ping else None  # z. B. @everyone oder @Rolle oder @User

    await interaction.response.send_message(content=content, embed=embed)


# ─── Bot starten ────────────────────────────────────────────────────

if __name__ == "__main__":
    TOKEN = os.getenv("DISCORD_TOKEN")
    if not TOKEN:
        TOKEN = "DEIN_TOKEN_HIER"  # ← für lokale Tests – bei Hosting besser .env / Railway Variable nutzen

    bot.run(TOKEN)
