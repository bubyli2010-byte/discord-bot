import discord
from discord.ext import commands
import os

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.command()
async def embed(ctx, titel, *, beschreibung):
    embed = discord.Embed(
        title=titel,
        description=beschreibung,
        color=discord.Color.blue()
    )
    embed.set_footer(text=f"Erstellt von {ctx.author.name}")
    await ctx.message.delete()
    await ctx.send(embed=embed)

bot.run(os.environ["TOKEN"])
```

**`requirements.txt`**
```
discord.py==2.3.2
```

---

**Benutzung auf Discord:**
```
!embed "Titel hier" Beschreibung hier
```

Beispiel:
```
!embed "Willkommen!" Dies ist ein Test Embed 
