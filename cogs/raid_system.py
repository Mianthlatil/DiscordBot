import discord
from discord import app_commands
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
    
    @app_commands.command(name="create-raid", description="Erstellt eine neue Raid-Anmeldung")
    @app_commands.describe(description="Beschreibung des Raids")
    async def create_raid_slash(self, interaction: discord.Interaction, description: str):
        """Slash command version of create_raid"""
        await interaction.response.defer()
        
        raid_id = f"raid_{int(interaction.created_at.timestamp())}"
        
        embed = discord.Embed(
            title="⚔️ Neue Raid-Anmeldung!",
            description=f"**Raid ID:** `{raid_id}`\n\n"
                       f"**Beschreibung:** {description}",
            color=0xFF6B35,
            timestamp=interaction.created_at
        )
        
        embed.add_field(
            name="👥 Rollen Gesucht",
            value="🛡️ **Tank** - Frontline Verteidigung\n"
                  "⚔️ **DPS** - Schaden verursachen\n"
                  "💚 **Healer** - Team unterstützen\n"
                  "🎯 **Support** - Buffs & Utility",
            inline=True
        )
        
        embed.add_field(
            name="📋 Anmeldung",
            value="Benutze `/register-raid` mit der Raid-ID\n"
                  "oder reagiere mit 🏜️ für Schnell-Anmeldung!",
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
        
        message = await interaction.followup.send(embed=embed)
        await message.add_reaction('🏜️')
    
    @app_commands.command(name="register-raid", description="Meldet sich für einen Raid an")
    @app_commands.describe(
        raid_id="Die ID des Raids",
        role_number="Rolle (1=Tank, 2=DPS, 3=Healer, 4=Support)",
        notes="Zusätzliche Notizen (optional)"
    )
    async def register_raid_slash(self, interaction: discord.Interaction, raid_id: str, role_number: int = None, notes: str = ""):
        """Slash command version of register_for_raid"""
        role_map = {
            1: "Tank 🛡️",
            2: "DPS ⚔️", 
            3: "Healer 💚",
            4: "Support 🎯"
        }
        
        if role_number and role_number not in role_map:
            await interaction.response.send_message("❌ Ungültige Rolle! Verfügbare Rollen: 1=Tank, 2=DPS, 3=Healer, 4=Support", ephemeral=True)
            return
        
        selected_role = role_map.get(role_number, "Flexibel 🔄")
        
        try:
            await self.db.register_for_raid(raid_id, interaction.user.id, interaction.user.display_name, selected_role, notes)
            
            embed = discord.Embed(
                title="✅ Raid-Anmeldung erfolgreich!",
                description=f"**Raid:** `{raid_id}`\n"
                           f"**Rolle:** {selected_role}\n"
                           f"**Notizen:** {notes if notes else 'Keine'}",
                color=0x4CAF50
            )
            embed.set_footer(text="Viel Erfolg beim Raid!")
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            await interaction.response.send_message(f"❌ Fehler bei der Anmeldung: {e}", ephemeral=True)
    
    @app_commands.command(name="raid-info", description="Zeigt Informationen und Anmeldungen für einen Raid")
    @app_commands.describe(raid_id="Die ID des Raids")
    async def raid_info_slash(self, interaction: discord.Interaction, raid_id: str):
        """Slash command version of raid_info"""
        await interaction.response.defer()
        
        registrations = await self.db.get_raid_registrations(raid_id)
        
        if not registrations:
            embed = discord.Embed(
                title="❌ Raid nicht gefunden",
                description=f"Keine Anmeldungen für Raid `{raid_id}` gefunden.",
                color=0xF44336
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        embed = discord.Embed(
            title=f"📊 Raid Informationen: {raid_id}",
            description=f"**Teilnehmer:** {len(registrations)}",
            color=0x3498DB
        )
        
        # Group by role
        role_groups = {}
        for user_id, username, role, notes, registered_at in registrations:
            if role not in role_groups:
                role_groups[role] = []
            role_groups[role].append((username, notes, registered_at))
        
        for role, members in role_groups.items():
            member_list = ""
            for username, notes, registered_at in members:
                note_text = f" - *{notes}*" if notes else ""
                member_list += f"• {username}{note_text}\n"
            
            embed.add_field(
                name=f"{role} ({len(members)})",
                value=member_list if member_list else "Niemand angemeldet",
                inline=True
            )
        
        embed.set_footer(text="Verwende /register-raid um dich anzumelden!")
        await interaction.followup.send(embed=embed)
    
    @app_commands.command(name="spice-crawl-signup", description="Erstellt eine Spice Crawling Anmeldung")
    async def spice_crawl_signup_slash(self, interaction: discord.Interaction):
        """Slash command version of spice_crawl_signup"""
        await interaction.response.defer()
        
        crawl_id = f"spice_crawl_{int(interaction.created_at.timestamp())}"
        
        embed = discord.Embed(
            title="🏜️ Spice Crawling Mission",
            description=f"**Mission ID:** `{crawl_id}`\n\n"
                       f"Sammle Spice in der gefährlichen Wüste von Arrakis!\n"
                       f"Hohe Belohnungen, aber auch hohe Risiken.",
            color=0xD2691E,
            timestamp=interaction.created_at
        )
        
        embed.add_field(
            name="🎯 Ziele",
            value="• Spice-Felder lokalisieren\n"
                  "• Spice-Harvester schützen\n"
                  "• Sandwürmer vermeiden\n"
                  "• Maximale Ausbeute erzielen",
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
        
        message = await interaction.followup.send(embed=embed)
        await message.add_reaction('🏜️')

async def setup(bot):
    await bot.add_cog(RaidSystem(bot))
