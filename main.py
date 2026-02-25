# main.py
import discord
from discord.ext import commands
import os
import datetime
from collections import deque, defaultdict

# KONFIGURATION – passe diese Werte an!
PREFIX = "!"
LOG_CHANNEL_ID = 123456789012345678  # ECHTE Channel-ID hier einfügen

# Anti-Raid Einstellungen
JOIN_THRESHOLD = 7
JOIN_WINDOW_SECONDS = 12

SPAM_THRESHOLD = 5
SPAM_WINDOW_SECONDS = 8

NEW_ACCOUNT_DAYS = 5

# BOT SETUP
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(
    command_prefix=PREFIX,
    intents=intents,
    help_command=None
)

# Speicher für Anti-Raid Erkennung
join_times = deque(maxlen=60)
user_messages = defaultdict(lambda: deque(maxlen=30))


@bot.event
async def on_ready():
    print(f"Bot online – {bot.user}")
    print(f"auf {len(bot.guilds)} Server(n)")
    print("bereit")


@bot.event
async def on_member_join(member: discord.Member):
    now = datetime.datetime.now(datetime.UTC)
    join_times.append(now)

    while join_times and (now - join_times[0]).total_seconds() > JOIN_WINDOW_SECONDS:
        join_times.popleft()

    # Massen-Join Erkennung
    if len(join_times) >= JOIN_THRESHOLD:
        channel = member.guild.get_channel(LOG_CHANNEL_ID)
        if channel:
            await channel.send(
                f"RAID-VERDACHT\n"
                f"{len(join_times)} Beitritte in <= {JOIN_WINDOW_SECONDS} Sekunden\n"
                f"Letzter: {member.mention}  ({member.id})"
            )

    # Verdächtiger neuer Account
    account_age_days = (now - member.created_at).days
    if account_age_days < NEW_ACCOUNT_DAYS:
        channel = member.guild.get_channel(LOG_CHANNEL_ID)
        if channel:
            await channel.send(
                f"Neuer Account – {member.mention}\n"
                f"Account erstellt vor {account_age_days} Tagen"
            )


@bot.event
async def on_message(message: discord.Message):
    if message.author.bot or not message.guild:
        return

    now = datetime.datetime.now(datetime.UTC)
    uid = message.author.id

    user_messages[uid].append(now)

    while user_messages[uid] and (now - user_messages[uid][0]).total_seconds() > SPAM_WINDOW_SECONDS:
        user_messages[uid].popleft()

    if len(user_messages[uid]) >= SPAM_THRESHOLD:
        try:
            await message.delete()
            await message.author.timeout(
                datetime.timedelta(minutes=10),
                reason="Automatischer Anti-Spam Timeout"
            )
            await message.channel.send(
                f"{message.author.mention} – Spam – 10 Minuten Timeout",
                delete_after=12
            )
        except discord.Forbidden:
            pass
        except Exception as e:
            print(f"Timeout fehlgeschlagen: {e}")

    await bot.process_commands(message)


# Beispiel Befehle
@bot.command(name="ping")
async def ping(ctx):
    latency = round(bot.latency * 1000)
    await ctx.send(f"Pong! {latency} ms")


@bot.command(name="status")
@commands.has_permissions(administrator=True)
async def status(ctx):
    await ctx.send(
        f"Anti-Raid Status\n"
        f"• Mass Join: >= {JOIN_THRESHOLD} in {JOIN_WINDOW_SECONDS} Sekunden\n"
        f"• Spam: >= {SPAM_THRESHOLD} Nachrichten in {SPAM_WINDOW_SECONDS} Sekunden\n"
        f"• Junge Accounts (< {NEW_ACCOUNT_DAYS} Tage) werden geloggt"
    )


# START
if __name__ == "__main__":
    TOKEN = os.getenv("DISCORD_TOKEN")
    if not TOKEN:
        print("FEHLER: Umgebungsvariable DISCORD_TOKEN nicht gefunden")
        exit(1)

    bot.run(TOKEN)
