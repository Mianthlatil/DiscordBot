import discord
from discord.ext import commands
import json
from database import Database
from utils.permissions import has_role_permission

class TempVoice(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = Database()
        
        # Load config
        with open('config.json', 'r', encoding='utf-8') as f:
            self.config = json.load(f)
        
        # Channel that triggers temp voice creation
        self.temp_voice_trigger = None
    
    @commands.command(name='set_temp_trigger', aliases=['temp_trigger'])
    @has_role_permission(['admin', 'moderator'])
    async def set_temp_trigger(self, ctx, channel: discord.VoiceChannel):
        """Setzt den Voice-Channel der temporäre Channels erstellt"""
        self.temp_voice_trigger = channel.id
        
        embed = discord.Embed(
            title="🔧 Temp Voice Trigger gesetzt",
            description=f"**{channel.name}** erstellt jetzt automatisch temporäre Voice-Channels!\n\n"
                       f"Wenn jemand diesem Channel beitritt, wird automatisch ein privater Channel erstellt.",
            color=0x4CAF50
        )
        await ctx.send(embed=embed)
    
    @commands.command(name='temp_voice', aliases=['temp'])
    async def create_temp_voice(self, ctx, *, name=None):
        """Erstellt einen temporären Voice-Channel"""
        guild = ctx.guild
        category_id = self.config['channels']['temp_voice_category']
        category = guild.get_channel(category_id) if category_id else None
        
        # Generate channel name
        if not name:
            name = self.config['temp_voice']['default_name'].format(user=ctx.author.display_name)
        
        # Create channel with permissions
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(connect=True, view_channel=True),
            ctx.author: discord.PermissionOverwrite(
                connect=True,
                manage_channels=True,
                manage_permissions=True,
                move_members=True,
                mute_members=True,
                deafen_members=True
            )
        }
        
        try:
            temp_channel = await guild.create_voice_channel(
                name=name,
                category=category,
                user_limit=self.config['temp_voice']['default_limit'],
                overwrites=overwrites,
                reason=f"Temporärer Voice-Channel von {ctx.author}"
            )
            
            # Add to database
            await self.db.add_temp_voice_channel(temp_channel.id, ctx.author.id)
            
            embed = discord.Embed(
                title="🔊 Temporärer Voice-Channel erstellt",
                description=f"**{temp_channel.name}** wurde erstellt!\n\n"
                           f"Du hast volle Kontrolle über diesen Channel.\n"
                           f"Er wird automatisch gelöscht wenn er leer ist.",
                color=0x4CAF50
            )
            embed.add_field(name="Channel", value=temp_channel.mention, inline=True)
            embed.add_field(name="Limit", value=f"{temp_channel.user_limit} Benutzer", inline=True)
            
            await ctx.send(embed=embed)
            
            # Move user to the new channel if they're in voice
            if ctx.author.voice and ctx.author.voice.channel:
                await ctx.author.move_to(temp_channel)
                
        except discord.HTTPException as e:
            await ctx.send(f"❌ Fehler beim Erstellen des Voice-Channels: {e}")
    
    @commands.command(name='temp_limit', aliases=['limit'])
    async def set_temp_limit(self, ctx, limit: int):
        """Ändert das Benutzerlimit eines temporären Voice-Channels"""
        if not ctx.author.voice or not ctx.author.voice.channel:
            await ctx.send("❌ Du musst dich in einem Voice-Channel befinden!")
            return
        
        channel = ctx.author.voice.channel
        owner_id = await self.db.get_temp_voice_owner(channel.id)
        
        if owner_id != ctx.author.id:
            await ctx.send("❌ Du bist nicht der Besitzer dieses Voice-Channels!")
            return
        
        if limit < 0 or limit > 99:
            await ctx.send("❌ Das Limit muss zwischen 0 und 99 liegen! (0 = unbegrenzt)")
            return
        
        try:
            await channel.edit(user_limit=limit, reason=f"Limit geändert von {ctx.author}")
            
            limit_text = "unbegrenzt" if limit == 0 else f"{limit} Benutzer"
            embed = discord.Embed(
                title="✅ Limit geändert",
                description=f"Das Benutzerlimit für **{channel.name}** wurde auf **{limit_text}** gesetzt!",
                color=0x4CAF50
            )
            await ctx.send(embed=embed)
            
        except discord.HTTPException as e:
            await ctx.send(f"❌ Fehler beim Ändern des Limits: {e}")
    
    @commands.command(name='temp_name', aliases=['rename'])
    async def rename_temp_channel(self, ctx, *, new_name):
        """Benennt einen temporären Voice-Channel um"""
        if not ctx.author.voice or not ctx.author.voice.channel:
            await ctx.send("❌ Du musst dich in einem Voice-Channel befinden!")
            return
        
        channel = ctx.author.voice.channel
        owner_id = await self.db.get_temp_voice_owner(channel.id)
        
        if owner_id != ctx.author.id:
            await ctx.send("❌ Du bist nicht der Besitzer dieses Voice-Channels!")
            return
        
        if len(new_name) > 100:
            await ctx.send("❌ Der Name darf maximal 100 Zeichen lang sein!")
            return
        
        old_name = channel.name
        
        try:
            await channel.edit(name=new_name, reason=f"Umbenannt von {ctx.author}")
            
            embed = discord.Embed(
                title="✅ Channel umbenannt",
                description=f"**{old_name}** wurde zu **{new_name}** umbenannt!",
                color=0x4CAF50
            )
            await ctx.send(embed=embed)
            
        except discord.HTTPException as e:
            await ctx.send(f"❌ Fehler beim Umbenennen: {e}")
    
    @commands.command(name='temp_kick', aliases=['tk'])
    async def kick_from_temp(self, ctx, member: discord.Member, *, reason="Kein Grund angegeben"):
        """Kickt einen Benutzer aus einem temporären Voice-Channel"""
        if not ctx.author.voice or not ctx.author.voice.channel:
            await ctx.send("❌ Du musst dich in einem Voice-Channel befinden!")
            return
        
        channel = ctx.author.voice.channel
        owner_id = await self.db.get_temp_voice_owner(channel.id)
        
        if owner_id != ctx.author.id:
            await ctx.send("❌ Du bist nicht der Besitzer dieses Voice-Channels!")
            return
        
        if member.voice and member.voice.channel == channel:
            try:
                await member.move_to(None, reason=f"Gekickt von {ctx.author}: {reason}")
                
                embed = discord.Embed(
                    title="👢 Benutzer gekickt",
                    description=f"**{member.display_name}** wurde aus dem Voice-Channel gekickt!",
                    color=0xFF6B6B
                )
                embed.add_field(name="Grund", value=reason, inline=False)
                await ctx.send(embed=embed)
                
            except discord.HTTPException as e:
                await ctx.send(f"❌ Fehler beim Kicken: {e}")
        else:
            await ctx.send("❌ Dieser Benutzer ist nicht in deinem Voice-Channel!")
    
    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        """Handle temp voice channel creation and deletion"""
        # Create temp voice when joining trigger channel
        if after.channel and after.channel.id == self.temp_voice_trigger:
            # Create temp voice for user
            guild = member.guild
            category_id = self.config['channels']['temp_voice_category']
            category = guild.get_channel(category_id) if category_id else None
            
            name = self.config['temp_voice']['default_name'].format(user=member.display_name)
            
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(connect=True, view_channel=True),
                member: discord.PermissionOverwrite(
                    connect=True,
                    manage_channels=True,
                    manage_permissions=True,
                    move_members=True,
                    mute_members=True,
                    deafen_members=True
                )
            }
            
            try:
                temp_channel = await guild.create_voice_channel(
                    name=name,
                    category=category,
                    user_limit=self.config['temp_voice']['default_limit'],
                    overwrites=overwrites,
                    reason=f"Auto-Temp Voice für {member}"
                )
                
                # Add to database
                await self.db.add_temp_voice_channel(temp_channel.id, member.id)
                
                # Move user to new channel
                await member.move_to(temp_channel)
                
            except discord.HTTPException:
                pass  # Failed to create or move
        
        # Delete empty temp voice channels
        if before.channel:
            owner_id = await self.db.get_temp_voice_owner(before.channel.id)
            if owner_id and len(before.channel.members) == 0:
                try:
                    await self.db.remove_temp_voice_channel(before.channel.id)
                    await before.channel.delete(reason="Temporärer Voice-Channel leer")
                except discord.HTTPException:
                    pass  # Failed to delete

async def setup(bot):
    await bot.add_cog(TempVoice(bot))
