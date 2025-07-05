import discord
from discord.ext import commands
import json
from database import Database
from utils.permissions import has_role_permission

class VoiceManagement(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = Database()
        
        # Load config
        with open('config.json', 'r', encoding='utf-8') as f:
            self.config = json.load(f)
        
        # Set to track locked channels and rage lock channels
        self.locked_channels = set()
        self.rage_lock_channels = set()
    
    @commands.command(name='lockvoice', aliases=['voicelock'])
    @has_role_permission(['admin', 'moderator'])
    async def lock_voice(self, ctx, channel: discord.VoiceChannel = None):
        """Sperrt einen Voice-Channel"""
        if not channel:
            if ctx.author.voice and ctx.author.voice.channel:
                channel = ctx.author.voice.channel
            else:
                await ctx.send("❌ Du musst einen Voice-Channel angeben oder dich in einem befinden!")
                return
        
        # Add to locked channels
        self.locked_channels.add(channel.id)
        
        # Set permissions to deny connect for @everyone
        await channel.set_permissions(
            ctx.guild.default_role, 
            connect=False,
            reason=f"Voice-Channel gesperrt von {ctx.author}"
        )
        
        embed = discord.Embed(
            title="🔒 Voice-Channel gesperrt",
            description=f"**{channel.name}** wurde gesperrt!\nNur Benutzer mit besonderen Berechtigungen können beitreten.",
            color=0xFF6B6B
        )
        await ctx.send(embed=embed)
    
    @commands.command(name='unlockvoice', aliases=['voiceunlock'])
    @has_role_permission(['admin', 'moderator'])
    async def unlock_voice(self, ctx, channel: discord.VoiceChannel = None):
        """Entsperrt einen Voice-Channel"""
        if not channel:
            if ctx.author.voice and ctx.author.voice.channel:
                channel = ctx.author.voice.channel
            else:
                await ctx.send("❌ Du musst einen Voice-Channel angeben oder dich in einem befinden!")
                return
        
        # Remove from locked channels
        self.locked_channels.discard(channel.id)
        
        # Reset permissions for @everyone
        await channel.set_permissions(
            ctx.guild.default_role, 
            connect=None,
            reason=f"Voice-Channel entsperrt von {ctx.author}"
        )
        
        embed = discord.Embed(
            title="🔓 Voice-Channel entsperrt",
            description=f"**{channel.name}** wurde entsperrt!\nAlle können wieder beitreten.",
            color=0x4CAF50
        )
        await ctx.send(embed=embed)
    
    @commands.command(name='ragelock')
    @has_role_permission(['admin', 'moderator'])
    async def rage_lock(self, ctx, channel: discord.VoiceChannel = None):
        """Aktiviert Rage Lock für einen Voice-Channel (kickt automatisch jeden der beitritt)"""
        if not channel:
            if ctx.author.voice and ctx.author.voice.channel:
                channel = ctx.author.voice.channel
            else:
                await ctx.send("❌ Du musst einen Voice-Channel angeben oder dich in einem befinden!")
                return
        
        if channel.id in self.rage_lock_channels:
            await ctx.send(f"❌ **{channel.name}** hat bereits Rage Lock aktiviert!")
            return
        
        self.rage_lock_channels.add(channel.id)
        
        embed = discord.Embed(
            title="😡 Rage Lock aktiviert",
            description=f"**{channel.name}** hat jetzt Rage Lock!\n"
                       f"Jeder der versucht beizutreten wird automatisch getrennt.",
            color=0x8B0000
        )
        await ctx.send(embed=embed)
    
    @commands.command(name='unragelock')
    @has_role_permission(['admin', 'moderator'])
    async def un_rage_lock(self, ctx, channel: discord.VoiceChannel = None):
        """Deaktiviert Rage Lock für einen Voice-Channel"""
        if not channel:
            if ctx.author.voice and ctx.author.voice.channel:
                channel = ctx.author.voice.channel
            else:
                await ctx.send("❌ Du musst einen Voice-Channel angeben oder dich in einem befinden!")
                return
        
        if channel.id not in self.rage_lock_channels:
            await ctx.send(f"❌ **{channel.name}** hat kein Rage Lock aktiviert!")
            return
        
        self.rage_lock_channels.remove(channel.id)
        
        embed = discord.Embed(
            title="😌 Rage Lock deaktiviert",
            description=f"**{channel.name}** hat kein Rage Lock mehr!\n"
                       f"Benutzer können wieder normal beitreten.",
            color=0x4CAF50
        )
        await ctx.send(embed=embed)
    
    @commands.command(name='moveall', aliases=['alle_verschieben'])
    @has_role_permission(['admin', 'moderator', 'raid_leader'])
    async def move_all(self, ctx, target_channel: discord.VoiceChannel):
        """Verschiebt alle Benutzer vom aktuellen Voice-Channel zum Ziel-Channel"""
        if not ctx.author.voice or not ctx.author.voice.channel:
            await ctx.send("❌ Du musst dich in einem Voice-Channel befinden!")
            return
        
        source_channel = ctx.author.voice.channel
        members_to_move = source_channel.members.copy()
        
        if not members_to_move:
            await ctx.send("❌ Keine Benutzer im Voice-Channel zum Verschieben!")
            return
        
        moved_count = 0
        failed_moves = []
        
        for member in members_to_move:
            try:
                await member.move_to(target_channel, reason=f"Move All von {ctx.author}")
                moved_count += 1
            except discord.HTTPException:
                failed_moves.append(member.display_name)
        
        embed = discord.Embed(
            title="🔄 Benutzer verschoben",
            description=f"**{moved_count}** Benutzer von **{source_channel.name}** zu **{target_channel.name}** verschoben!",
            color=0x4CAF50
        )
        
        if failed_moves:
            embed.add_field(
                name="⚠️ Fehler beim Verschieben",
                value=", ".join(failed_moves),
                inline=False
            )
        
        await ctx.send(embed=embed)
    
    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        """Handle voice state changes for rage lock and voice activity tracking"""
        # Handle rage lock
        if after.channel and after.channel.id in self.rage_lock_channels:
            # Check if user has permission to bypass rage lock
            if not any(role.name.lower() in ['admin', 'moderator', 'raid_leader'] for role in member.roles):
                try:
                    await member.move_to(None, reason="Rage Lock aktiviert")
                    
                    # Try to send DM to user
                    try:
                        embed = discord.Embed(
                            title="😡 Rage Lock!",
                            description=f"Du wurdest aus **{after.channel.name}** getrennt!\n"
                                       f"Dieser Channel hat Rage Lock aktiviert.",
                            color=0x8B0000
                        )
                        await member.send(embed=embed)
                    except discord.Forbidden:
                        pass  # Can't send DM
                        
                except discord.HTTPException:
                    pass  # Failed to disconnect user

async def setup(bot):
    await bot.add_cog(VoiceManagement(bot))
