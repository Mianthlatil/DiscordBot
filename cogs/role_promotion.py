import discord
from discord.ext import commands, tasks
import json
from datetime import datetime, timedelta
from database import Database
from utils.permissions import has_role_permission

class RolePromotion(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = Database()
        
        # Load config
        with open('config.json', 'r', encoding='utf-8') as f:
            self.config = json.load(f)
        
        # Start the promotion check task
        self.check_promotions.start()
    
    def cog_unload(self):
        self.check_promotions.cancel()
    
    @tasks.loop(seconds=300)  # Check every 5 minutes
    async def check_promotions(self):
        """Check for users eligible for promotion"""
        await self.bot.wait_until_ready()
        
        required_minutes = self.config['voice_promotion']['hours_required'] * 60
        
        # Get all guilds (assuming single guild bot)
        for guild in self.bot.guilds:
            rekrut_role_id = self.config['roles']['rekrut']
            member_role_id = self.config['roles']['member']
            
            if not rekrut_role_id or not member_role_id:
                continue
            
            rekrut_role = guild.get_role(rekrut_role_id)
            member_role = guild.get_role(member_role_id)
            
            if not rekrut_role or not member_role:
                continue
            
            # Check members with Rekrut role
            for member in rekrut_role.members:
                voice_data = await self.db.get_voice_activity(member.id)
                
                if voice_data['total_minutes'] >= required_minutes:
                    try:
                        # Remove Rekrut role and add Member role
                        await member.remove_roles(rekrut_role, reason="Automatische Beförderung nach 24h Voice")
                        await member.add_roles(member_role, reason="Automatische Beförderung nach 24h Voice")
                        
                        # Send congratulations
                        embed = discord.Embed(
                            title="🎉 Herzlichen Glückwunsch zur Beförderung!",
                            description=f"**{member.display_name}** wurde automatisch zum **Member** befördert!\n\n"
                                       f"Du hast **{voice_data['total_minutes']:,} Minuten** in Voice-Channels verbracht.\n"
                                       f"Willkommen im inneren Kreis der Gilde!",
                            color=0x4CAF50,
                            timestamp=datetime.now()
                        )
                        embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
                        embed.add_field(
                            name="🏆 Neue Vorteile",
                            value="• Zugang zu Member-Channels\n"
                                  "• Höhere Raid-Priorität\n"
                                  "• Spezielle Member-Belohnungen\n"
                                  "• Erweiterte Bot-Befehle",
                            inline=False
                        )
                        
                        # Try to send DM first
                        try:
                            await member.send(embed=embed)
                        except discord.Forbidden:
                            # If DM fails, send in a general channel
                            if guild.system_channel:
                                await guild.system_channel.send(f"{member.mention}", embed=embed)
                        
                        # Award promotion bonus
                        promotion_bonus = 1000
                        await self.db.update_user_balance(member.id, promotion_bonus)
                        
                        print(f"✅ {member.display_name} wurde automatisch zum Member befördert!")
                        
                    except discord.HTTPException as e:
                        print(f"❌ Fehler bei der Beförderung von {member.display_name}: {e}")
    
    @commands.command(name='voice_stats', aliases=['vstats'])
    async def voice_stats(self, ctx, member: discord.Member = None):
        """Zeigt Voice-Aktivitäts-Statistiken"""
        target = member or ctx.author
        voice_data = await self.db.get_voice_activity(target.id)
        
        total_minutes = voice_data['total_minutes']
        hours = total_minutes // 60
        minutes = total_minutes % 60
        
        required_minutes = self.config['voice_promotion']['hours_required'] * 60
        progress = min(100, (total_minutes / required_minutes) * 100)
        remaining_minutes = max(0, required_minutes - total_minutes)
        remaining_hours = remaining_minutes // 60
        remaining_mins = remaining_minutes % 60
        
        embed = discord.Embed(
            title="🎙️ Voice-Aktivitäts-Statistiken",
            color=0x3498DB
        )
        embed.set_author(
            name=target.display_name,
            icon_url=target.avatar.url if target.avatar else target.default_avatar.url
        )
        
        embed.add_field(
            name="⏱️ Gesamt Voice-Zeit",
            value=f"**{hours:,}h {minutes}m**\n({total_minutes:,} Minuten)",
            inline=True
        )
        
        embed.add_field(
            name="🎯 Für Member-Rolle",
            value=f"**{self.config['voice_promotion']['hours_required']}h** benötigt",
            inline=True
        )
        
        embed.add_field(
            name="📊 Fortschritt",
            value=f"**{progress:.1f}%**\n{'█' * int(progress/10)}{'░' * (10-int(progress/10))}",
            inline=False
        )
        
        if remaining_minutes > 0:
            embed.add_field(
                name="⏳ Verbleibende Zeit",
                value=f"**{remaining_hours}h {remaining_mins}m**",
                inline=True
            )
        else:
            embed.add_field(
                name="✅ Berechtigung",
                value="**Bereit für Member-Rolle!**",
                inline=True
            )
        
        # Show current session if in voice
        if voice_data['session_start']:
            session_start = datetime.fromisoformat(voice_data['session_start'])
            session_duration = datetime.now() - session_start
            session_minutes = int(session_duration.total_seconds() / 60)
            
            embed.add_field(
                name="🔴 Aktuelle Session",
                value=f"**{session_minutes // 60}h {session_minutes % 60}m**",
                inline=True
            )
        
        await ctx.send(embed=embed)
    
    @commands.command(name='force_promote', aliases=['promote'])
    @has_role_permission(['admin', 'moderator'])
    async def force_promote(self, ctx, member: discord.Member):
        """Befördert einen Benutzer manuell zum Member"""
        rekrut_role_id = self.config['roles']['rekrut']
        member_role_id = self.config['roles']['member']
        
        if not rekrut_role_id or not member_role_id:
            await ctx.send("❌ Rollen sind nicht konfiguriert!")
            return
        
        rekrut_role = ctx.guild.get_role(rekrut_role_id)
        member_role = ctx.guild.get_role(member_role_id)
        
        if not rekrut_role or not member_role:
            await ctx.send("❌ Rollen nicht gefunden!")
            return
        
        if rekrut_role not in member.roles:
            await ctx.send(f"❌ {member.display_name} hat nicht die Rekrut-Rolle!")
            return
        
        if member_role in member.roles:
            await ctx.send(f"❌ {member.display_name} ist bereits ein Member!")
            return
        
        try:
            await member.remove_roles(rekrut_role, reason=f"Manuelle Beförderung von {ctx.author}")
            await member.add_roles(member_role, reason=f"Manuelle Beförderung von {ctx.author}")
            
            # Award promotion bonus
            promotion_bonus = 1000
            await self.db.update_user_balance(member.id, promotion_bonus)
            
            embed = discord.Embed(
                title="🎉 Manuelle Beförderung",
                description=f"**{member.display_name}** wurde manuell zum **Member** befördert!",
                color=0x4CAF50
            )
            embed.set_footer(text=f"Befördert von {ctx.author.display_name}")
            
            await ctx.send(embed=embed)
            
            # Notify the promoted user
            try:
                promotion_embed = discord.Embed(
                    title="🎉 Du wurdest befördert!",
                    description=f"Du wurdest manuell zum **Member** befördert!\n"
                               f"Befördert von: **{ctx.author.display_name}**\n\n"
                               f"Du hast **{promotion_bonus:,}** Spice als Beförderungsbonus erhalten!",
                    color=0x4CAF50
                )
                await member.send(embed=promotion_embed)
            except discord.Forbidden:
                pass  # Can't send DM
            
        except discord.HTTPException as e:
            await ctx.send(f"❌ Fehler bei der Beförderung: {e}")
    
    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        """Track voice activity for promotion system"""
        now = datetime.now()
        
        # User joined a voice channel
        if after.channel and not before.channel:
            await self.db.update_voice_activity(member.id, session_start=now.isoformat())
            
            # Award voice reward
            voice_reward = self.config['economy']['voice_reward_per_hour'] // 12  # Per 5 minutes
            await self.db.update_user_balance(member.id, voice_reward)
        
        # User left voice completely
        elif before.channel and not after.channel:
            voice_data = await self.db.get_voice_activity(member.id)
            
            if voice_data['session_start']:
                session_start = datetime.fromisoformat(voice_data['session_start'])
                session_duration = now - session_start
                session_minutes = int(session_duration.total_seconds() / 60)
                
                # Update total minutes and clear session
                await self.db.update_voice_activity(member.id, minutes_to_add=session_minutes)
        
        # User switched channels (update session start time)
        elif before.channel and after.channel and before.channel != after.channel:
            # Calculate time in previous channel
            voice_data = await self.db.get_voice_activity(member.id)
            
            if voice_data['session_start']:
                session_start = datetime.fromisoformat(voice_data['session_start'])
                session_duration = now - session_start
                session_minutes = int(session_duration.total_seconds() / 60)
                
                # Update minutes and start new session
                await self.db.update_voice_activity(member.id, minutes_to_add=session_minutes)
                await self.db.update_voice_activity(member.id, session_start=now.isoformat())

async def setup(bot):
    await bot.add_cog(RolePromotion(bot))
