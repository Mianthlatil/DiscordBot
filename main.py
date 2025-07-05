import discord
from discord.ext import commands
import asyncio
import json
import os
from database import Database

# Bot configuration
intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True
intents.members = True
intents.guilds = True

# Load configuration
with open('config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)

bot = commands.Bot(command_prefix=config['prefix'], intents=intents)

@bot.event
async def on_ready():
    print(f'{bot.user} ist bereit! (Bot ist online)')
    print(f'Verbunden mit {len(bot.guilds)} Server(n)')
    
    # Initialize database
    db = Database()
    await db.initialize()
    
    # Load all cogs
    cogs_to_load = [
        'cogs.command_overview',
        'cogs.economy',
        'cogs.voice_management', 
        'cogs.raid_system',
        'cogs.modmail',
        'cogs.temp_voice',
        'cogs.role_promotion',
        'cogs.event_system'
    ]
    
    for cog in cogs_to_load:
        try:
            await bot.load_extension(cog)
            print(f'✓ {cog} erfolgreich geladen')
        except Exception as e:
            print(f'✗ Fehler beim Laden von {cog}: {e}')
    
    # Sync slash commands
    try:
        synced = await bot.tree.sync()
        print(f'✓ {len(synced)} Slash Commands synchronisiert')
    except Exception as e:
        print(f'✗ Fehler beim Synchronisieren der Slash Commands: {e}')

@bot.event
async def on_command_error(ctx, error):
    """Global error handler"""
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"❌ Fehlender Parameter: `{error.param.name}`")
    elif isinstance(error, commands.CommandNotFound):
        return  # Ignore command not found errors
    elif isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ Du hast nicht die erforderlichen Berechtigungen für diesen Befehl.")
    elif isinstance(error, commands.BotMissingPermissions):
        await ctx.send("❌ Dem Bot fehlen die erforderlichen Berechtigungen.")
    else:
        await ctx.send(f"❌ Ein unerwarteter Fehler ist aufgetreten: {str(error)}")
        print(f"Unbehandelter Fehler: {error}")

if __name__ == "__main__":
    # Get bot token from environment variable
    token = os.getenv('DISCORD_TOKEN')
    if not token:
        print("❌ DISCORD_TOKEN Umgebungsvariable nicht gesetzt!")
        exit(1)
    
    bot.run(token)
