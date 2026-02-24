import discord
from discord import app_commands
import os

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

@tree.command(name="embed", description="Erstelle ein Embed")
@app_commands.describe(titel="Der Titel des Embeds", beschreibung="Der Text des Embeds")
async def embed(interaction: discord.Interaction, titel: str, beschreibung: str):
    em = discord.Embed(
        title=titel,
        description=beschreibung,
        color=discord.Color.blue()
    )
    em.set_footer(text=f"Erstellt von {interaction.user.name}")
    await interaction.response.send_message(embed=em)

@client.event
async def on_ready():
    await tree.sync()
    print(f"Bot ist online als {client.user}")

client.run(os.environ["TOKEN"])
