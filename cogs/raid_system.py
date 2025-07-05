import discord
from discord.ext import commands
import json
from datetime import datetime, timedelta
from database import Database
from utils.permissions import has_role_permission

class RaidSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = Database()
        
        # Load config
        with open('config.json', 'r', encoding='utf-8') as f:
            self.config = json.load(f)
        
        # Available roles for raids
        self.raid_roles = [
            "🗡️ DPS (Damage Dealer)",
            "🛡️ Tank", 
            "❤️ Healer/Support",
            "🎯 Sniper",
            "🔧 Engineer",
            "👥 Flex (Beliebig)"
        ]
    
    @commands.command(name='createraid', aliases=['raid_erstellen'])
    @has_role_permission(['admin', 'moderator', 'raid_leader'])
    async def create_raid(self, ctx, *, description):
        """Erstellt eine neue Raid-Anmeldung"""
        # Generate unique raid ID
        raid_id = f"raid_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        embed = discord.Embed(
            title="⚔️ Neuer Dune Awakening Raid",
            description=description,
            color=0xFF8C00,
            timestamp=datetime.now()
        )
        
        embed.add_field(
            name="📝 Anmeldung",
            value="Reagiere mit den entsprechenden Emojis um dich anzumelden:\n\n"
                  "🗡️ - DPS (Damage Dealer)\n"
                  "🛡️ - Tank\n" 
                  "❤️ - Healer/Support\n"
                  "🎯 - Sniper\n"
                  "🔧 - Engineer\n"
                  "👥 - Flex (Beliebig)",
            inline=False
        )
        
        embed.add_field(
            name="ℹ️ Raid-ID",
            value=f"`{raid_id}`",
            inline=True
        )
        
        embed.add_field(
            name="👤 Erstellt von",
            value=ctx.author.mention,
            inline=True
        )
        
        embed.set_footer(text="Verwende !raid_info <ID> für Details | !anmelden <ID> <Rolle> für Anmeldung")
        
        message = await ctx.send(embed=embed)
        
        # Add reaction buttons
        reactions = ['🗡️', '🛡️', '❤️', '🎯', '🔧', '👥']
        for reaction in reactions:
            await message.add_reaction(reaction)
        
        # Store raid info (you might want to add this to database later)
        await ctx.send(f"✅ Raid erstellt! ID: `{raid_id}`")
    
    @commands.command(name='anmelden', aliases=['register', 'signup'])
    async def register_for_raid(self, ctx, raid_id: str, role_number: int = None, *, notes=""):
        """Meldet sich für einen Raid an"""
        if role_number is None or role_number < 1 or role_number > len(self.raid_roles):
            roles_list = "\n".join([f"{i+1}. {role}" for i, role in enumerate(self.raid_roles)])
            
            embed = discord.Embed(
                title="❌ Ungültige Rolle",
                description=f"Bitte wähle eine gültige Rolle (1-{len(self.raid_roles)}):\n\n{roles_list}",
                color=0xFF6B6B
            )
            await ctx.send(embed=embed)
            return
        
        selected_role = self.raid_roles[role_number - 1]
        
        # Register user for raid
        success = await self.db.register_for_raid(
            raid_id, ctx.author.id, ctx.author.display_name, selected_role, notes
        )
        
        if success:
            embed = discord.Embed(
                title="✅ Erfolgreich angemeldet!",
                description=f"Du bist für Raid `{raid_id}` angemeldet!",
                color=0x4CAF50
            )
            embed.add_field(name="Rolle", value=selected_role, inline=True)
            if notes:
                embed.add_field(name="Notizen", value=notes, inline=False)
        else:
            embed = discord.Embed(
                title="❌ Bereits angemeldet!",
                description=f"Du bist bereits für Raid `{raid_id}` angemeldet!",
                color=0xFF6B6B
            )
        
        await ctx.send(embed=embed)
    
    @commands.command(name='raid_info', aliases=['raidinfo'])
    async def raid_info(self, ctx, raid_id: str):
        """Zeigt Informationen und Anmeldungen für einen Raid"""
        registrations = await self.db.get_raid_registrations(raid_id)
        
        if not registrations:
            await ctx.send(f"❌ Keine Anmeldungen für Raid `{raid_id}` gefunden!")
            return
        
        embed = discord.Embed(
            title=f"⚔️ Raid Anmeldungen: {raid_id}",
            color=0xFF8C00,
            timestamp=datetime.now()
        )
        
        # Group by role
        role_groups = {}
        for user_id, username, role, notes, registered_at in registrations:
            if role not in role_groups:
                role_groups[role] = []
            role_groups[role].append((username, notes, registered_at))
        
        for role, members in role_groups.items():
            member_list = []
            for username, notes, registered_at in members:
                member_info = f"• **{username}**"
                if notes:
                    member_info += f" - _{notes}_"
                member_list.append(member_info)
            
            embed.add_field(
                name=f"{role} ({len(members)})",
                value="\n".join(member_list) if member_list else "Niemand angemeldet",
                inline=False
            )
        
        embed.set_footer(text=f"Gesamt: {len(registrations)} Spieler angemeldet")
        await ctx.send(embed=embed)
    
    @commands.command(name='spice_crawl', aliases=['spicecrawl'])
    async def spice_crawl_signup(self, ctx):
        """Erstellt eine Spice Crawling Anmeldung"""
        embed = discord.Embed(
            title="🏜️ Spice Crawling Expedition",
            description="Bereite dich auf eine gefährliche Expedition in die Spice-Felder vor!\n\n"
                       "**Was dich erwartet:**\n"
                       "• Harvester-Schutz\n"
                       "• Spice-Sammlung\n"
                       "• Sandwurm-Verteidigung\n"
                       "• Reiche Belohnungen\n\n"
                       "**Voraussetzungen:**\n"
                       "• Mindestlevel 20\n"
                       "• Eigenes Fahrzeug empfohlen\n"
                       "• Voice-Chat erforderlich",
            color=0xDEB887,
            timestamp=datetime.now()
        )
        
        embed.add_field(
            name="🎯 Benötigte Rollen",
            value="🚗 **Fahrer** (2-3)\n"
                  "🔫 **Kämpfer** (4-6)\n" 
                  "⛏️ **Sammler** (2-3)\n"
                  "👁️ **Späher** (1-2)",
            inline=True
        )
        
        embed.add_field(
            name="⏰ Zeitplan",
            value="**Start:** In 30 Minuten\n"
                  "**Dauer:** 1-2 Stunden\n"
                  "**Treffpunkt:** Hauptbasis",
            inline=True
        )
        
        embed.add_field(
            name="💰 Belohnungen",
            value="• 500 Spice (Bot-Währung)\n"
                  "• Geteilte Spice-Erträge\n"
                  "• XP-Bonus\n"
                  "• Spezielle Ausrüstung",
            inline=False
        )
        
        embed.set_footer(text="Reagiere mit 🏜️ um teilzunehmen!")
        
        message = await ctx.send(embed=embed)
        await message.add_reaction('🏜️')
    
    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        """Handle raid registration reactions"""
        if user.bot:
            return
        
        # Map reactions to roles
        reaction_roles = {
            '🗡️': "🗡️ DPS (Damage Dealer)",
            '🛡️': "🛡️ Tank",
            '❤️': "❤️ Healer/Support", 
            '🎯': "🎯 Sniper",
            '🔧': "🔧 Engineer",
            '👥': "👥 Flex (Beliebig)"
        }
        
        if str(reaction.emoji) in reaction_roles:
            # Extract raid ID from message (this is simplified - you might want to store this differently)
            message = reaction.message
            if "Raid-ID" in message.embeds[0].description if message.embeds else False:
                # This is a basic implementation - you'd want to properly parse the raid ID
                selected_role = reaction_roles[str(reaction.emoji)]
                
                # Auto-register user (simplified)
                try:
                    embed = discord.Embed(
                        title="✅ Schnell-Anmeldung",
                        description=f"Du wurdest als **{selected_role}** registriert!\n"
                                   f"Verwende `!raid_info <ID>` für Details.",
                        color=0x4CAF50
                    )
                    await user.send(embed=embed)
                except discord.Forbidden:
                    pass  # Can't send DM

async def setup(bot):
    await bot.add_cog(RaidSystem(bot))
