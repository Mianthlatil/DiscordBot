
import discord
from discord.ext import commands
from discord import app_commands
import json
import os

class Setup(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def update_config(self, key_path, value):
        """Update configuration file with new value"""
        with open('config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # Navigate to nested key
        current = config
        keys = key_path.split('.')
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        current[keys[-1]] = value
        
        with open('config.json', 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4, ensure_ascii=False)

    @app_commands.command(name="setup", description="Bot-Konfiguration einrichten")
    @app_commands.describe(
        component="Welche Komponente konfigurieren",
        guild_id="Server ID (für Slash Commands)",
        prefix="Bot Command Prefix"
    )
    @app_commands.choices(component=[
        app_commands.Choice(name="Grundeinstellungen", value="basic"),
        app_commands.Choice(name="Rollen", value="roles"),
        app_commands.Choice(name="Kanäle", value="channels"),
        app_commands.Choice(name="Voice Promotion", value="voice_promo"),
        app_commands.Choice(name="Temp Voice", value="temp_voice"),
        app_commands.Choice(name="Command Berechtigungen", value="permissions"),
        app_commands.Choice(name="Alle anzeigen", value="show_all")
    ])
    async def setup_command(self, interaction: discord.Interaction, component: str, guild_id: str = None, prefix: str = None):
        """Setup command for bot configuration"""
        
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Du benötigst Administrator-Rechte für diesen Befehl!", ephemeral=True)
            return

        if component == "show_all":
            await self.show_current_config(interaction)
            return

        if component == "basic":
            await self.setup_basic(interaction, guild_id, prefix)
        elif component == "roles":
            await self.setup_roles(interaction)
        elif component == "channels":
            await self.setup_channels(interaction)
        elif component == "voice_promo":
            await self.setup_voice_promotion(interaction)
        elif component == "temp_voice":
            await self.setup_temp_voice(interaction)
        elif component == "permissions":
            await self.setup_permissions(interaction)

    async def show_current_config(self, interaction):
        """Show current configuration"""
        with open('config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)

        embed = discord.Embed(
            title="🔧 Aktuelle Bot-Konfiguration",
            color=0x3498DB,
            timestamp=discord.utils.utcnow()
        )

        # Basic settings
        embed.add_field(
            name="⚙️ Grundeinstellungen",
            value=f"**Prefix:** `{config.get('prefix', 'Nicht gesetzt')}`\n"
                  f"**Guild ID:** `{config.get('guild_id') or 'Nicht gesetzt'}`",
            inline=False
        )

        # Roles
        roles = config.get('roles', {})
        role_status = []
        for role_name, role_id in roles.items():
            status = "✅" if role_id else "❌"
            role_status.append(f"{status} {role_name.title()}")
        
        embed.add_field(
            name="👥 Rollen-Status",
            value="\n".join(role_status) if role_status else "Keine Rollen konfiguriert",
            inline=True
        )

        # Channels
        channels = config.get('channels', {})
        channel_status = []
        for channel_name, channel_id in channels.items():
            status = "✅" if channel_id else "❌"
            channel_status.append(f"{status} {channel_name.replace('_', ' ').title()}")
        
        embed.add_field(
            name="📝 Kanal-Status",
            value="\n".join(channel_status) if channel_status else "Keine Kanäle konfiguriert",
            inline=True
        )

        # Voice promotion
        voice_promo = config.get('voice_promotion', {})
        embed.add_field(
            name="🎖️ Voice Promotion",
            value=f"**Stunden benötigt:** {voice_promo.get('hours_required', 24)}\n"
                  f"**Check Intervall:** {voice_promo.get('check_interval', 300)}s",
            inline=False
        )

        # Command permissions
        permissions = config.get('command_permissions', {})
        perm_status = "✅ Konfiguriert" if permissions else "❌ Standard verwendet"
        embed.add_field(
            name="🔐 Command Berechtigungen",
            value=f"**Status:** {perm_status}\n"
                  f"**Commands konfiguriert:** {len(permissions)}",
            inline=True
        )

        embed.set_footer(text="Verwende /setup um Einstellungen zu ändern")
        await interaction.response.send_message(embed=embed)

    async def setup_basic(self, interaction, guild_id, prefix):
        """Setup basic configuration"""
        embed = discord.Embed(
            title="⚙️ Grundeinstellungen",
            color=0x4CAF50
        )

        if guild_id:
            try:
                guild_id_int = int(guild_id)
                await self.update_config('guild_id', guild_id_int)
                embed.add_field(name="Guild ID", value=f"✅ Gesetzt auf: `{guild_id}`", inline=False)
            except ValueError:
                embed.add_field(name="Guild ID", value="❌ Ungültige Guild ID", inline=False)

        if prefix:
            await self.update_config('prefix', prefix)
            embed.add_field(name="Prefix", value=f"✅ Gesetzt auf: `{prefix}`", inline=False)

        if not guild_id and not prefix:
            embed.description = "Nutze die Parameter um Werte zu setzen:\n`/setup component:Grundeinstellungen guild_id:DEINE_SERVER_ID prefix:!`"

        await interaction.response.send_message(embed=embed)

    async def setup_roles(self, interaction):
        """Setup roles with dropdown"""
        view = RoleSetupView(self)
        embed = discord.Embed(
            title="👥 Rollen-Setup",
            description="Wähle eine Rolle aus dem Dropdown-Menü aus und erwähne dann die entsprechende Discord-Rolle:",
            color=0xFF8C00
        )
        await interaction.response.send_message(embed=embed, view=view)

    async def setup_channels(self, interaction):
        """Setup channels with dropdown"""
        view = ChannelSetupView(self)
        embed = discord.Embed(
            title="📝 Kanal-Setup",
            description="Wähle einen Kanaltyp aus dem Dropdown-Menü aus und erwähne dann den entsprechenden Discord-Kanal:",
            color=0x9B59B6
        )
        await interaction.response.send_message(embed=embed, view=view)

    async def setup_voice_promotion(self, interaction):
        """Setup voice promotion settings"""
        view = VoicePromoSetupView(self)
        embed = discord.Embed(
            title="🎖️ Voice Promotion Setup",
            description="Konfiguriere die automatische Beförderung von Rekrut zu Member:",
            color=0xE74C3C
        )
        await interaction.response.send_message(embed=embed, view=view)

    async def setup_temp_voice(self, interaction):
        """Setup temporary voice settings"""
        view = TempVoiceSetupView(self)
        embed = discord.Embed(
            title="🔊 Temporäre Voice Kanäle Setup",
            description="Konfiguriere die Einstellungen für temporäre Voice Kanäle:",
            color=0x1ABC9C
        )
        await interaction.response.send_message(embed=embed, view=view)

    async def setup_permissions(self, interaction):
        """Setup command permissions"""
        view = PermissionSetupView(self)
        embed = discord.Embed(
            title="🔐 Command Berechtigungen Setup",
            description="Konfiguriere welche Rollen welche Befehle verwenden können:\n\n"
                       "**Standard Hierarchie:**\n"
                       "👑 Admin > 🛡️ Moderator > ⚔️ Raid Leader > 🥈 Member > 🥉 Rekrut",
            color=0x8E44AD
        )
        await interaction.response.send_message(embed=embed, view=view)

class RoleSetupView(discord.ui.View):
    def __init__(self, setup_cog):
        super().__init__(timeout=300)
        self.setup_cog = setup_cog

    @discord.ui.select(
        placeholder="Wähle eine Rolle zum Konfigurieren...",
        options=[
            discord.SelectOption(label="Rekrut", value="rekrut", emoji="🥉"),
            discord.SelectOption(label="Member", value="member", emoji="🥈"),
            discord.SelectOption(label="Moderator", value="moderator", emoji="🛡️"),
            discord.SelectOption(label="Admin", value="admin", emoji="👑"),
            discord.SelectOption(label="Raid Leader", value="raid_leader", emoji="⚔️"),
        ]
    )
    async def role_select(self, interaction: discord.Interaction, select: discord.ui.Select):
        role_name = select.values[0]
        await interaction.response.send_modal(RoleModal(self.setup_cog, role_name))

class RoleModal(discord.ui.Modal):
    def __init__(self, setup_cog, role_name):
        super().__init__(title=f"{role_name.title()} Rolle konfigurieren")
        self.setup_cog = setup_cog
        self.role_name = role_name

        self.role_input = discord.ui.TextInput(
            label="Rolle erwähnen oder ID eingeben",
            placeholder="@RolleName oder 123456789012345678",
            required=True
        )
        self.add_item(self.role_input)

    async def on_submit(self, interaction: discord.Interaction):
        role_input = self.role_input.value.strip()
        
        # Try to extract role ID
        role_id = None
        if role_input.startswith('<@&') and role_input.endswith('>'):
            role_id = int(role_input[3:-1])
        else:
            try:
                role_id = int(role_input)
            except ValueError:
                await interaction.response.send_message("❌ Ungültige Rolle! Bitte erwähne die Rolle oder gib die ID ein.", ephemeral=True)
                return

        # Verify role exists
        role = interaction.guild.get_role(role_id)
        if not role:
            await interaction.response.send_message("❌ Rolle nicht gefunden!", ephemeral=True)
            return

        await self.setup_cog.update_config(f'roles.{self.role_name}', role_id)
        
        embed = discord.Embed(
            title="✅ Rolle konfiguriert",
            description=f"**{self.role_name.title()}** wurde auf {role.mention} gesetzt!",
            color=0x4CAF50
        )
        await interaction.response.send_message(embed=embed)

class ChannelSetupView(discord.ui.View):
    def __init__(self, setup_cog):
        super().__init__(timeout=300)
        self.setup_cog = setup_cog

    @discord.ui.select(
        placeholder="Wähle einen Kanaltyp zum Konfigurieren...",
        options=[
            discord.SelectOption(label="ModMail Kategorie", value="modmail_category", emoji="📬"),
            discord.SelectOption(label="Temp Voice Kategorie", value="temp_voice_category", emoji="🔊"),
            discord.SelectOption(label="Raid Ankündigungen", value="raid_announcements", emoji="⚔️"),
        ]
    )
    async def channel_select(self, interaction: discord.Interaction, select: discord.ui.Select):
        channel_name = select.values[0]
        await interaction.response.send_modal(ChannelModal(self.setup_cog, channel_name))

class ChannelModal(discord.ui.Modal):
    def __init__(self, setup_cog, channel_name):
        super().__init__(title=f"{channel_name.replace('_', ' ').title()} konfigurieren")
        self.setup_cog = setup_cog
        self.channel_name = channel_name

        self.channel_input = discord.ui.TextInput(
            label="Kanal erwähnen oder ID eingeben",
            placeholder="#kanal-name oder 123456789012345678",
            required=True
        )
        self.add_item(self.channel_input)

    async def on_submit(self, interaction: discord.Interaction):
        channel_input = self.channel_input.value.strip()
        
        # Try to extract channel ID
        channel_id = None
        if channel_input.startswith('<#') and channel_input.endswith('>'):
            channel_id = int(channel_input[2:-1])
        else:
            try:
                channel_id = int(channel_input)
            except ValueError:
                await interaction.response.send_message("❌ Ungültiger Kanal! Bitte erwähne den Kanal oder gib die ID ein.", ephemeral=True)
                return

        # Verify channel exists
        channel = interaction.guild.get_channel(channel_id)
        if not channel:
            await interaction.response.send_message("❌ Kanal nicht gefunden!", ephemeral=True)
            return

        await self.setup_cog.update_config(f'channels.{self.channel_name}', channel_id)
        
        embed = discord.Embed(
            title="✅ Kanal konfiguriert",
            description=f"**{self.channel_name.replace('_', ' ').title()}** wurde auf {channel.mention} gesetzt!",
            color=0x4CAF50
        )
        await interaction.response.send_message(embed=embed)

class VoicePromoSetupView(discord.ui.View):
    def __init__(self, setup_cog):
        super().__init__(timeout=300)
        self.setup_cog = setup_cog

    @discord.ui.button(label="Stunden ändern", style=discord.ButtonStyle.primary, emoji="⏰")
    async def change_hours(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(VoiceHoursModal(self.setup_cog))

    @discord.ui.button(label="Check-Intervall ändern", style=discord.ButtonStyle.secondary, emoji="🔄")
    async def change_interval(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(VoiceIntervalModal(self.setup_cog))

class VoiceHoursModal(discord.ui.Modal):
    def __init__(self, setup_cog):
        super().__init__(title="Voice Promotion Stunden")
        self.setup_cog = setup_cog

        self.hours_input = discord.ui.TextInput(
            label="Stunden bis zur Beförderung",
            placeholder="24",
            required=True,
            max_length=3
        )
        self.add_item(self.hours_input)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            hours = int(self.hours_input.value)
            if hours <= 0:
                raise ValueError()
            
            await self.setup_cog.update_config('voice_promotion.hours_required', hours)
            
            embed = discord.Embed(
                title="✅ Stunden aktualisiert",
                description=f"Voice Promotion Stunden auf **{hours}** gesetzt!",
                color=0x4CAF50
            )
            await interaction.response.send_message(embed=embed)
        except ValueError:
            await interaction.response.send_message("❌ Bitte gib eine gültige Anzahl Stunden ein!", ephemeral=True)

class VoiceIntervalModal(discord.ui.Modal):
    def __init__(self, setup_cog):
        super().__init__(title="Voice Check Intervall")
        self.setup_cog = setup_cog

        self.interval_input = discord.ui.TextInput(
            label="Check-Intervall in Sekunden",
            placeholder="300",
            required=True,
            max_length=4
        )
        self.add_item(self.interval_input)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            interval = int(self.interval_input.value)
            if interval < 60:
                raise ValueError("Intervall muss mindestens 60 Sekunden sein")
            
            await self.setup_cog.update_config('voice_promotion.check_interval', interval)
            
            embed = discord.Embed(
                title="✅ Intervall aktualisiert",
                description=f"Check-Intervall auf **{interval}** Sekunden gesetzt!",
                color=0x4CAF50
            )
            await interaction.response.send_message(embed=embed)
        except ValueError as e:
            await interaction.response.send_message(f"❌ {str(e)}", ephemeral=True)

class TempVoiceSetupView(discord.ui.View):
    def __init__(self, setup_cog):
        super().__init__(timeout=300)
        self.setup_cog = setup_cog

    @discord.ui.button(label="Standard Name", style=discord.ButtonStyle.primary, emoji="📝")
    async def change_name(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(TempVoiceNameModal(self.setup_cog))

    @discord.ui.button(label="Standard Limit", style=discord.ButtonStyle.secondary, emoji="👥")
    async def change_limit(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(TempVoiceLimitModal(self.setup_cog))

class TempVoiceNameModal(discord.ui.Modal):
    def __init__(self, setup_cog):
        super().__init__(title="Temp Voice Standard Name")
        self.setup_cog = setup_cog

        self.name_input = discord.ui.TextInput(
            label="Standard Kanalname",
            placeholder="{user}'s Channel",
            required=True,
            max_length=100
        )
        self.add_item(self.name_input)

    async def on_submit(self, interaction: discord.Interaction):
        name = self.name_input.value.strip()
        
        await self.setup_cog.update_config('temp_voice.default_name', name)
        
        embed = discord.Embed(
            title="✅ Standard Name aktualisiert",
            description=f"Temp Voice Standard Name auf **{name}** gesetzt!\n\n"
                       "**Tipp:** Verwende `{user}` für den Benutzernamen",
            color=0x4CAF50
        )
        await interaction.response.send_message(embed=embed)

class TempVoiceLimitModal(discord.ui.Modal):
    def __init__(self, setup_cog):
        super().__init__(title="Temp Voice Standard Limit")
        self.setup_cog = setup_cog

        self.limit_input = discord.ui.TextInput(
            label="Standard Benutzerlimit",
            placeholder="100",
            required=True,
            max_length=2
        )
        self.add_item(self.limit_input)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            limit = int(self.limit_input.value)
            if limit < 1 or limit > 99:
                raise ValueError("Limit muss zwischen 1 und 99 sein")
            
            await self.setup_cog.update_config('temp_voice.default_limit', limit)
            
            embed = discord.Embed(
                title="✅ Standard Limit aktualisiert",
                description=f"Temp Voice Standard Limit auf **{limit}** gesetzt!",
                color=0x4CAF50
            )
            await interaction.response.send_message(embed=embed)
        except ValueError as e:
            await interaction.response.send_message(f"❌ {str(e)}", ephemeral=True)

class PermissionSetupView(discord.ui.View):
    def __init__(self, setup_cog):
        super().__init__(timeout=300)
        self.setup_cog = setup_cog

    @discord.ui.select(
        placeholder="Wähle eine Command-Kategorie...",
        options=[
            discord.SelectOption(label="Economy Commands", value="economy", emoji="💰"),
            discord.SelectOption(label="Event System", value="events", emoji="⚔️"),
            discord.SelectOption(label="Voice Management", value="voice", emoji="🎙️"),
            discord.SelectOption(label="Temp Voice", value="temp_voice", emoji="🔊"),
            discord.SelectOption(label="Raid System", value="raids", emoji="🏜️"),
            discord.SelectOption(label="ModMail", value="modmail", emoji="📬"),
            discord.SelectOption(label="Role Promotion", value="promotion", emoji="🎖️"),
            discord.SelectOption(label="Alle zurücksetzen", value="reset_all", emoji="🔄"),
        ]
    )
    async def category_select(self, interaction: discord.Interaction, select: discord.ui.Select):
        category = select.values[0]
        
        if category == "reset_all":
            await interaction.response.send_modal(ResetPermissionsModal(self.setup_cog))
        else:
            await interaction.response.send_message(
                view=CommandPermissionView(self.setup_cog, category),
                embed=self.create_category_embed(category),
                ephemeral=True
            )

    def create_category_embed(self, category):
        """Create embed for specific command category"""
        category_info = {
            "economy": {
                "title": "💰 Economy Commands",
                "commands": ["balance", "leaderboard", "give", "take"],
                "description": "Spice-System Befehle"
            },
            "events": {
                "title": "⚔️ Event System", 
                "commands": ["event", "event-edit", "event_info", "crawler", "carrier"],
                "description": "Event-Management Befehle"
            },
            "voice": {
                "title": "🎙️ Voice Management",
                "commands": ["lockvoice", "unlockvoice", "ragelock", "moveall", "voice_stats"],
                "description": "Voice-Channel Verwaltung"
            },
            "temp_voice": {
                "title": "🔊 Temp Voice",
                "commands": ["temp_voice", "temp_limit", "temp_name", "temp_kick"],
                "description": "Temporäre Voice-Channels"
            },
            "raids": {
                "title": "🏜️ Raid System",
                "commands": ["createraid", "anmelden", "raid_info", "spice_crawl"],
                "description": "Raid-Management"
            },
            "modmail": {
                "title": "📬 ModMail",
                "commands": ["modmail", "reply", "close"],
                "description": "Support-Ticket System"
            },
            "promotion": {
                "title": "🎖️ Role Promotion",
                "commands": ["force_promote", "voice_stats"],
                "description": "Automatische Beförderungen"
            }
        }
        
        info = category_info[category]
        embed = discord.Embed(
            title=info["title"],
            description=f"{info['description']}\n\n**Commands in dieser Kategorie:**\n" + 
                       "\n".join([f"• `{cmd}`" for cmd in info["commands"]]),
            color=0x8E44AD
        )
        return embed

class CommandPermissionView(discord.ui.View):
    def __init__(self, setup_cog, category):
        super().__init__(timeout=300)
        self.setup_cog = setup_cog
        self.category = category

    @discord.ui.select(
        placeholder="Welche Rollen sollen Zugriff haben?",
        options=[
            discord.SelectOption(label="Nur Admins", value="admin_only", emoji="👑"),
            discord.SelectOption(label="Admins + Moderatoren", value="admin_mod", emoji="🛡️"),
            discord.SelectOption(label="Admins + Mods + Raid Leader", value="admin_mod_raid", emoji="⚔️"),
            discord.SelectOption(label="Alle außer Rekruts", value="no_rekrut", emoji="🥈"),
            discord.SelectOption(label="Alle Rollen", value="all_roles", emoji="👥"),
            discord.SelectOption(label="Individuell konfigurieren", value="custom", emoji="⚙️"),
        ]
    )
    async def permission_select(self, interaction: discord.Interaction, select: discord.ui.Select):
        permission_level = select.values[0]
        
        if permission_level == "custom":
            await interaction.response.send_modal(CustomPermissionModal(self.setup_cog, self.category))
        else:
            await self.set_category_permissions(interaction, permission_level)

    async def set_category_permissions(self, interaction, permission_level):
        """Set permissions for entire command category"""
        permission_mapping = {
            "admin_only": ["admin"],
            "admin_mod": ["admin", "moderator"],
            "admin_mod_raid": ["admin", "moderator", "raid_leader"],
            "no_rekrut": ["admin", "moderator", "raid_leader", "member"],
            "all_roles": ["admin", "moderator", "raid_leader", "member", "rekrut"]
        }
        
        roles = permission_mapping[permission_level]
        
        # Get commands for this category
        category_commands = {
            "economy": ["balance", "leaderboard", "give", "take"],
            "events": ["event", "event-edit", "event_info", "crawler", "carrier"],
            "voice": ["lockvoice", "unlockvoice", "ragelock", "moveall", "voice_stats"],
            "temp_voice": ["temp_voice", "temp_limit", "temp_name", "temp_kick"],
            "raids": ["createraid", "anmelden", "raid_info", "spice_crawl"],
            "modmail": ["modmail", "reply", "close"],
            "promotion": ["force_promote", "voice_stats"]
        }
        
        commands = category_commands.get(self.category, [])
        
        # Update config for each command
        for command in commands:
            await self.setup_cog.update_config(f'command_permissions.{command}', roles)
        
        embed = discord.Embed(
            title="✅ Berechtigungen aktualisiert",
            description=f"**Kategorie:** {self.category.title()}\n"
                       f"**Befehle:** {len(commands)}\n"
                       f"**Berechtigte Rollen:** {', '.join([r.title() for r in roles])}",
            color=0x4CAF50
        )
        await interaction.response.send_message(embed=embed)

class CustomPermissionModal(discord.ui.Modal):
    def __init__(self, setup_cog, category):
        super().__init__(title=f"Custom Permissions: {category.title()}")
        self.setup_cog = setup_cog
        self.category = category

        self.command_input = discord.ui.TextInput(
            label="Command Name",
            placeholder="z.B. balance, give, lockvoice",
            required=True
        )
        self.add_item(self.command_input)

        self.roles_input = discord.ui.TextInput(
            label="Erlaubte Rollen (kommagetrennt)",
            placeholder="admin,moderator,member",
            required=True,
            style=discord.TextStyle.paragraph
        )
        self.add_item(self.roles_input)

    async def on_submit(self, interaction: discord.Interaction):
        command = self.command_input.value.strip()
        roles_str = self.roles_input.value.strip()
        
        # Parse roles
        roles = [role.strip().lower() for role in roles_str.split(',')]
        valid_roles = ['admin', 'moderator', 'raid_leader', 'member', 'rekrut']
        
        # Validate roles
        invalid_roles = [role for role in roles if role not in valid_roles]
        if invalid_roles:
            await interaction.response.send_message(
                f"❌ Ungültige Rollen: {', '.join(invalid_roles)}\n"
                f"**Gültige Rollen:** {', '.join(valid_roles)}", 
                ephemeral=True
            )
            return
        
        # Update config
        await self.setup_cog.update_config(f'command_permissions.{command}', roles)
        
        embed = discord.Embed(
            title="✅ Command Berechtigung gesetzt",
            description=f"**Command:** `{command}`\n"
                       f"**Berechtigte Rollen:** {', '.join([r.title() for r in roles])}",
            color=0x4CAF50
        )
        await interaction.response.send_message(embed=embed)

class ResetPermissionsModal(discord.ui.Modal):
    def __init__(self, setup_cog):
        super().__init__(title="Alle Berechtigungen zurücksetzen")
        self.setup_cog = setup_cog

        self.confirm_input = discord.ui.TextInput(
            label="Bestätigung (schreibe: RESET)",
            placeholder="RESET",
            required=True,
            max_length=5
        )
        self.add_item(self.confirm_input)

    async def on_submit(self, interaction: discord.Interaction):
        if self.confirm_input.value.upper() != "RESET":
            await interaction.response.send_message("❌ Bestätigung fehlgeschlagen!", ephemeral=True)
            return

        # Reset all command permissions
        await self.setup_cog.update_config('command_permissions', {})
        
        embed = discord.Embed(
            title="✅ Berechtigungen zurückgesetzt",
            description="Alle Command-Berechtigungen wurden auf Standard zurückgesetzt.\n"
                       "Der Bot verwendet jetzt wieder die eingebauten Berechtigungen.",
            color=0x4CAF50
        )
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Setup(bot))
