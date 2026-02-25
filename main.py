# requirements.txt Inhalt (pip install -r requirements.txt)
# discord.py>=2.4.0
# python-dotenv

import asyncio
import datetime
import logging
from collections import defaultdict, deque
from typing import Dict, Deque

import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv
import os

load_dotenv()

# ---------------- KONFIGURATION ----------------
TOKEN = os.getenv("DISCORD_TOKEN")
if not TOKEN:
    raise ValueError("DISCORD_TOKEN fehlt in .env!")

# Anti-Raid Einstellungen (anpassen!)
RAID_SETTINGS = {
    "join_per_10s_threshold": 8,          # ≥8 Joins in 10 Sekunden → Raid-Alarm
    "new_account_days": 7,                # Accounts jünger als 7 Tage gelten als verdächtig
    "mass_mention_threshold": 6,          # ≥6 Erwähnungen in einer Nachricht
    "spam_messages_per_8s": 5,            # ≥5 Nachrichten in 8 Sekunden
    "log_channel_id": 123456789012345678, # ID deines Log-Kanals (ändern!)
    "auto_verify_new_members": True,      # Neue Member bekommen automatisch Verified-Rolle später?
}

# ---------------- LOGGING ----------------
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(name)s → %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("AntiRaidBot")

intents = discord.Intents.default()
intents.members = True          # Wichtig für Join-Events & Member-Updates
intents.message_content = True  # Für Spam-Erkennung

bot = commands.Bot(
    command_prefix="!",
    intents=intents,
    help_command=None,
    case_insensitive=True
)

# ---------------- ANTI-RAID DATEN ----------------
join_times: Deque[datetime.datetime] = deque(maxlen=30)
recent_messages: Dict[int, Deque[datetime.datetime]] = defaultdict(lambda: deque(maxlen=15))
mentions_count: Dict[int, int] = defaultdict(int)


@bot.event
async def on_ready():
    print(f"━┫ Eingeloggt als {bot.user} ({bot.user.id})")
    print(f"━┫ Serveranzahl   : {len(bot.guilds)}")
    try:
        synced = await bot.tree.sync()
        print(f"━┫ {len(synced)} Slash-Commands registriert")
    except Exception as e:
        print(f"Slash-Command Sync Fehler: {e}")


# ─── RAID DETECTION: Massen-Joins ────────────────────────────────
@bot.event
async def on_member_join(member: discord.Member):
    now = datetime.datetime.now(datetime.UTC)
    join_times.append(now)

    # Alte Einträge entfernen (älter als 10 Sekunden)
    while join_times and (now - join_times[0]).total_seconds() > 10:
        join_times.popleft()

    if len(join_times) >= RAID_SETTINGS["join_per_10s_threshold"]:
        await handle_raid_alert(member.guild, f"**MASS JOIN RAID** – {len(join_times)} Joins in <10s")

        # Hier kannst du später härtere Maßnahmen einbauen:
        # await lockdown_server(member.guild)

    # Verdächtiger neuer Account?
    if (now - member.created_at).days < RAID_SETTINGS["new_account_days"]:
        await log_suspicious_member(member, "Neuer Account (< 7 Tage)")


async def log_suspicious_member(member: discord.Member, reason: str):
    channel = member.guild.get_channel(RAID_SETTINGS["log_channel_id"])
    if not channel:
        return

    embed = discord.Embed(
        title="Verdächtiger Beitritt",
        color=0xe74c3c,
        timestamp=datetime.datetime.now(datetime.UTC)
    )
    embed.add_field(name="User", value=f"{member} ({member.id})", inline=True)
    embed.add_field(name="Account erstellt", value=f"<t:{int(member.created_at.timestamp())}:R>", inline=True)
    embed.add_field(name="Grund", value=reason, inline=False)
    embed.set_thumbnail(url=member.display_avatar.url)

    await channel.send(embed=embed)


# ─── RAID DETECTION: Spam + Massen-Mention ───────────────────────
@bot.event
async def on_message(message: discord.Message):
    if message.author.bot or not message.guild:
        return

    now = datetime.datetime.now(datetime.UTC)
    author_id = message.author.id

    # Spam Detection
    recent_messages[author_id].append(now)
    while recent_messages[author_id] and (now - recent_messages[author_id][0]).total_seconds() > 8:
        recent_messages[author_id].popleft()

    if len(recent_messages[author_id]) >= RAID_SETTINGS["spam_messages_per_8s"]:
        await message.delete()
        await message.channel.send(f"{message.author.mention} → **Stop spammen!** (Timeout 30s)", delete_after=8)
        try:
            await message.author.timeout(datetime.timedelta(seconds=30), reason="Automatischer Anti-Spam Timeout")
        except:
            pass

    # Mass Mention
    if len(message.mentions) >= RAID_SETTINGS["mass_mention_threshold"]:
        await message.delete()
        await message.channel.send(f"{message.author.mention} → **Zu viele Erwähnungen!**", delete_after=10)
        try:
            await message.author.timeout(datetime.timedelta(minutes=5), reason="Mass-Mention Spam")
        except:
            pass

    await bot.process_commands(message)


# ─── Beispiel: Lockdown bei Raid ─────────────────────────────────
async def handle_raid_alert(guild: discord.Guild, reason: str):
    channel = guild.get_channel(RAID_SETTINGS["log_channel_id"])
    if channel:
        await channel.send(f"@here **RAID ALARM** – {reason}")

    # Optional: sehr einfacher Lockdown (nur Textkanäle)
    # for ch in guild.text_channels:
    #     if ch.permissions_for(guild.default_role).send_messages:
    #         await ch.set_permissions(guild.default_role, send_messages=False, reason="Raid Lockdown")


# ─── Slash Command: Status ───────────────────────────────────────
@bot.tree.command(name="anti_raid_status", description="Zeigt aktuelle Anti-Raid Einstellungen")
@app_commands.default_permissions(administrator=True)
async def status(interaction: discord.Interaction):
    e = discord.Embed(title="Anti-Raid Status", color=0x2ecc71)
    e.add_field(name="Join Threshold (10s)", value=RAID_SETTINGS["join_per_10s_threshold"], inline=True)
    e.add_field(name="Neuer Account <", value=f"{RAID_SETTINGS['new_account_days']} Tage", inline=True)
    e.add_field(name="Spam Msg/8s", value=RAID_SETTINGS["spam_messages_per_8s"], inline=True)
    e.add_field(name="Mass Mention", value=f">={RAID_SETTINGS['mass_mention_threshold']} Erwähnungen", inline=True)
    await interaction.response.send_message(embed=e, ephemeral=True)


# ─── Start ───────────────────────────────────────────────────────
if __name__ == "__main__":
    bot.run(TOKEN, log_handler=None)
