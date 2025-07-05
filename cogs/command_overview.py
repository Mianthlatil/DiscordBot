import discord
from discord.ext import commands
from discord import app_commands
import json

class CommandOverview(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
        # Load config
        with open('config.json', 'r', encoding='utf-8') as f:
            self.config = json.load(f)
    
    @commands.command(name='commands', aliases=['hilfe', 'befehle'])
    async def commands_overview(self, ctx):
        """Zeigt alle verfügbaren Befehle an"""
        await self._send_help(ctx.send, ctx.author)
    
    @app_commands.command(name="help", description="Zeigt alle verfügbaren Bot-Befehle an")
    async def help_slash(self, interaction: discord.Interaction):
        """Slash command version of help"""
        await self._send_help(interaction.response.send_message, interaction.user)
    
    async def _send_help(self, send_func, user):
        """Send help message for both command and slash command"""
        embed = discord.Embed(
            title="🤖 Muad'Dib Bot - Command Übersicht",
            description="Dein Dune Awakening Gilden-Management Bot\n\n"
                       "**Verfügbar als:** `/slash` und `!prefix` Commands",
            color=0xFF8C00,
            timestamp=discord.utils.utcnow()
        )
        
        # Economy Commands (daily removed)
        embed.add_field(
            name="💰 Economy System",
            value="`/balance` - Spice-Guthaben anzeigen\n"
                  "`/leaderboard` - Reichste Spieler anzeigen\n"
                  "`/give` - Spice vergeben (Mods)\n"
                  "`/take` - Spice entziehen (Mods)",
            inline=False
        )
        
        # Event System (updated with event-edit)
        embed.add_field(
            name="⚔️ Event System",
            value="`/event` - Neues Event mit Titel erstellen (Mods)\n"
                  "`/event-edit` - Crawler/Carrier zuweisen (Mods)\n"
                  "`/event_info` - Event-Anmeldungen anzeigen\n"
                  "`/crawler` - Spieler als Crawler anmelden (Mods)\n"
                  "`/carrier` - Spieler als Carrier anmelden (Mods)\n"
                  "🗡️🛡️ - Reaktions-Anmeldung für Attack/Def",
            inline=False
        )
        
        # Voice Management
        embed.add_field(
            name="🎙️ Voice Management",
            value="`/lockvoice` - Voice-Channel sperren (Mods)\n"
                  "`/unlockvoice` - Voice-Channel entsperren (Mods)\n"
                  "`/ragelock` - Auto-Kick aktivieren (Mods)\n"
                  "`/moveall` - Alle Benutzer verschieben (Mods)\n"
                  "`/voice_stats` - Voice-Aktivität anzeigen",
            inline=False
        )
        
        # Temporary Voice
        embed.add_field(
            name="🔊 Temporäre Voice Channels",
            value="`/temp_voice` - Eigenen Channel erstellen\n"
                  "`/temp_limit` - Benutzerlimit ändern\n"
                  "`/temp_name` - Channel umbenennen\n"
                  "`/temp_kick` - Benutzer kicken",
            inline=False
        )
        
        # Raid System
        embed.add_field(
            name="🏜️ Raid System",
            value="`/createraid` - Raid erstellen (Mods)\n"
                  "`/anmelden` - Für Raid anmelden\n"
                  "`/raid_info` - Raid-Details anzeigen\n"
                  "`/spice_crawl` - Spice Crawling Event",
            inline=False
        )
        
        # Role Promotion
        embed.add_field(
            name="🎖️ Automatische Beförderung",
            value="`/voice_stats` - Fortschritt zur Member-Rolle\n"
                  "`/force_promote` - Manuelle Beförderung (Mods)\n"
                  "**Auto:** Rekrut → Member nach 24h Voice",
            inline=False
        )
        
        # ModMail
        embed.add_field(
            name="📬 ModMail System",
            value="`!modmail <nachricht>` - Ticket erstellen (DM)\n"
                  "`/reply` - Auf Ticket antworten (Mods)\n"
                  "`/close` - Ticket schließen (Mods)",
            inline=False
        )
        
        embed.add_field(
            name="ℹ️ Zusätzliche Infos",
            value="**Prefix:** `!` für Text-Commands\n"
                  "**Slash:** `/` für Slash-Commands\n"
                  "**Mods:** Moderator/Admin Berechtigung erforderlich\n"
                  "**Auto:** Läuft automatisch im Hintergrund",
            inline=False
        )
        
        embed.set_footer(text="Die Spice muss fließen! | Dune Awakening Guild Bot")
        embed.set_thumbnail(url=self.bot.user.avatar.url if self.bot.user.avatar else None)
        
        await send_func(embed=embed)

async def setup(bot):
    await bot.add_cog(CommandOverview(bot))