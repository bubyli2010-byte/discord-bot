import discord
from discord.ext import commands
import os

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.command()
async def embed(ctx, titel, *, beschreibung):
    em = discord.Embed(
        title=titel,
        description=beschreibung,
        color=discord.Color.blue()
    )
    em.set_footer(text=f"Erstellt von {ctx.author.name}")
    await ctx.message.delete()
    await ctx.send(embed=em)

bot.run(os.environ["TOKEN"])
