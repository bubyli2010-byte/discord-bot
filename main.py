# main.py
import discord
from discord.ext import commands
import asyncio

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(
    command_prefix="!",
    intents=intents,
    help_command=None,
    case_insensitive=True
)

# Globale Variable für RP-Status (später persistent machen, z. B. JSON)
RP_STATUS = {"open": False}

# ─── Hilfsfunktion: Embed für Status ────────────────────────────────
def status_embed():
    color = discord.Color.green() if RP_STATUS["open"] else discord.Color.red()
    desc = "Geöffnet – Code-Posten erlaubt" if RP_STATUS["open"] else "Geschlossen – warte auf Öffnung"
    
    embed = discord.Embed(
        title="RP-Status",
        description=desc,
        color=color,
        timestamp=discord.utils.utcnow()
    )
    embed.set_footer(text="!rpstatus zum Umschalten | !rpcode zum Posten")
    return embed


# ─── !rpstatus – Status anzeigen + Umschalten ──────────────────────
@bot.command(name="rpstatus")
@commands.has_permissions(manage_guild=True)  # nur Admins/Mods
async def rpstatus_cmd(ctx):
    embed = status_embed()
    
    view = discord.ui.View(timeout=60)
    btn_open = discord.ui.Button(label="Geöffnet", style=discord.ButtonStyle.green, custom_id="open")
    btn_closed = discord.ui.Button(label="Geschlossen", style=discord.ButtonStyle.red, custom_id="closed")
    
    async def button_callback(interaction: discord.Interaction):
        if interaction.user != ctx.author:
            await interaction.response.send_message("Nur der, der den Befehl ausgeführt hat, darf klicken.", ephemeral=True)
            return
            
        RP_STATUS["open"] = (interaction.data["custom_id"] == "open")
        
        new_embed = status_embed()
        await interaction.message.edit(embed=new_embed, view=None)
        await interaction.response.send_message(f"RP-Status → **{'Geöffnet' if RP_STATUS['open'] else 'Geschlossen'}**", ephemeral=True)
    
    btn_open.callback = button_callback
    btn_closed.callback = button_callback
    
    view.add_item(btn_open)
    view.add_item(btn_closed)
    
    msg = await ctx.send(embed=embed, view=view)
    
    # Timeout-Handling
    try:
        await asyncio.sleep(60)
        await msg.edit(view=None)
    except:
        pass


# ─── !rpcode – Interaktives Formular zum Code-Posten ───────────────
@bot.command(name="rpcode")
async def rpcode_cmd(ctx):
    if not RP_STATUS["open"]:
        embed = discord.Embed(
            title="RP ist derzeit geschlossen",
            description="Momentan können keine Codes gepostet werden.",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed, delete_after=12)
        return

    # ── Formular starten ───────────────────────────────────────────
    questions = [
        ("**Code / Link / Invite** (z. B. abc-123-xyz oder https://...)", 120),
        ("**Kurze Beschreibung** (was erwartet die Leute?)", 180),
        ("**Wann startet es?** (Uhrzeit / Datum / bald / jetzt)", 90),
        ("**Wer soll gepingt werden?** (@everyone, @Rolle, @User – oder leer lassen)", 60)
    ]
    
    answers = []
    cancel = False
    
    status_msg = await ctx.send(embed=discord.Embed(
        description="**RP-Code Formular gestartet**\nAntworte einfach nacheinander im Chat.\nSchreibe `cancel` um abzubrechen.",
        color=discord.Color.blue()
    ))

    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel

    for i, (frage, timeout) in enumerate(questions, 1):
        embed = discord.Embed(
            title=f"Frage {i}/{len(questions)}",
            description=frage,
            color=discord.Color.blurple()
        )
        embed.set_footer(text=f"Antworte im Chat | max. {timeout} Sekunden | cancel = abbrechen")
        
        await status_msg.edit(embed=embed)

        try:
            msg = await bot.wait_for("message", check=check, timeout=timeout)
            
            if msg.content.lower() == "cancel":
                cancel = True
                break
                
            answers.append(msg.content.strip())
            
        except asyncio.TimeoutError:
            await status_msg.edit(embed=discord.Embed(
                description="Zeit abgelaufen – Formular abgebrochen.",
                color=discord.Color.red()
            ))
            return

    await status_msg.delete(delay=1)

    if cancel:
        await ctx.send("Formular abgebrochen.", delete_after=8)
        return

    if len(answers) < len(questions):
        await ctx.send("Nicht alle Fragen beantwortet – abgebrochen.")
        return

    # ── Embed zusammenbauen ────────────────────────────────────────
    code, beschreibung, zeit, ping = answers

    embed = discord.Embed(
        title="Neuer RP-Code / Event",
        description=f"**Code / Link:**\n```\n{code}\n```",
        color=discord.Color.green(),
        timestamp=discord.utils.utcnow()
    )
    
    embed.add_field(name="Beschreibung", value=beschreibung or "Keine Angabe", inline=False)
    embed.add_field(name="Startzeit", value=zeit or "Nicht angegeben", inline=True)
    embed.set_footer(text=f"von {ctx.author} | Status: Geöffnet")

    content = ping if ping and ping.strip() else None

    await ctx.send(content=content, embed=embed)


# ─── Bot Start ──────────────────────────────────────────────────────
@bot.event
async def on_ready():
    print(f"RP-Bot online → {bot.user}")
    print("Prefix-Befehle: !rpstatus  |  !rpcode")


if __name__ == "__main__":
    bot.run("DEIN_TOKEN_HIER")   # oder os.getenv("DISCORD_TOKEN")
