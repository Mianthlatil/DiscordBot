import discord
from discord.ext import commands
import json
import asyncio
from datetime import datetime
from database import Database
from utils.permissions import has_role_permission

class ModMail(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = Database()
        
        # Load config
        with open('config.json', 'r', encoding='utf-8') as f:
            self.config = json.load(f)
    
    @commands.command(name='modmail', aliases=['mm'])
    async def create_modmail(self, ctx, *, message):
        """Erstellt ein neues ModMail Ticket"""
        if ctx.guild:
            await ctx.send("❌ Dieser Befehl kann nur in privaten Nachrichten verwendet werden!")
            return
        
        user = ctx.author
        
        # Check if user already has an open modmail thread
        async with aiosqlite.connect(self.db.db_path) as db:
            cursor = await db.execute(
                "SELECT channel_id, status FROM modmail_threads WHERE user_id = ? AND status = 'open'", 
                (user.id,)
            )
            existing = await cursor.fetchone()
        
        if existing:
            channel = self.bot.get_channel(existing[0])
            if channel:
                await ctx.send(f"❌ Du hast bereits ein offenes ModMail Ticket! <#{existing[0]}>")
                return
        
        # Get the guild (assuming single guild bot)
        guild = self.bot.guilds[0] if self.bot.guilds else None
        if not guild:
            await ctx.send("❌ Fehler: Bot ist mit keinem Server verbunden!")
            return
        
        # Get modmail category
        category_id = self.config['channels']['modmail_category']
        category = guild.get_channel(category_id) if category_id else None
        
        # Create modmail channel
        channel_name = f"modmail-{user.name}-{user.discriminator}"
        
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            user: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }
        
        # Add permissions for moderators and admins
        for role_name in ['moderator', 'admin']:
            role_id = self.config['roles'].get(role_name)
            if role_id:
                role = guild.get_role(role_id)
                if role:
                    overwrites[role] = discord.PermissionOverwrite(
                        read_messages=True, 
                        send_messages=True,
                        manage_messages=True
                    )
        
        try:
            modmail_channel = await guild.create_text_channel(
                channel_name,
                category=category,
                overwrites=overwrites,
                reason=f"ModMail von {user}"
            )
        except discord.HTTPException as e:
            await ctx.send(f"❌ Fehler beim Erstellen des ModMail Kanals: {e}")
            return
        
        # Store in database
        async with aiosqlite.connect(self.db.db_path) as db:
            await db.execute('''
                INSERT INTO modmail_threads (user_id, channel_id, status)
                VALUES (?, ?, 'open')
            ''', (user.id, modmail_channel.id))
            await db.commit()
        
        # Send initial messages
        embed = discord.Embed(
            title="📬 Neues ModMail Ticket",
            description=f"**Benutzer:** {user.mention} ({user})\n"
                       f"**User ID:** {user.id}\n"
                       f"**Erstellt:** {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}",
            color=0x3498DB,
            timestamp=datetime.now()
        )
        embed.add_field(
            name="💬 Erste Nachricht",
            value=message[:1024] + ("..." if len(message) > 1024 else ""),
            inline=False
        )
        embed.set_thumbnail(url=user.avatar.url if user.avatar else user.default_avatar.url)
        embed.set_footer(text="Verwende !close um dieses Ticket zu schließen")
        
        await modmail_channel.send(embed=embed)
        
        # Confirmation to user
        confirmation_embed = discord.Embed(
            title="✅ ModMail Ticket erstellt!",
            description=f"Dein Ticket wurde erfolgreich erstellt!\n"
                       f"Die Moderatoren werden sich bald bei dir melden.\n\n"
                       f"**Ticket Kanal:** {modmail_channel.mention}",
            color=0x4CAF50
        )
        await ctx.send(embed=confirmation_embed)
        
        # Ping moderators (optional)
        mod_role_id = self.config['roles'].get('moderator')
        if mod_role_id:
            mod_role = guild.get_role(mod_role_id)
            if mod_role:
                await modmail_channel.send(f"{mod_role.mention} - Neues ModMail Ticket!")
    
    @commands.command(name='reply', aliases=['r'])
    @has_role_permission(['admin', 'moderator'])
    async def reply_modmail(self, ctx, *, message):
        """Antwortet auf ein ModMail Ticket"""
        # Check if this is a modmail channel
        async with aiosqlite.connect(self.db.db_path) as db:
            cursor = await db.execute(
                "SELECT user_id FROM modmail_threads WHERE channel_id = ? AND status = 'open'",
                (ctx.channel.id,)
            )
            result = await cursor.fetchone()
        
        if not result:
            await ctx.send("❌ Dies ist kein aktives ModMail Ticket!")
            return
        
        user_id = result[0]
        user = self.bot.get_user(user_id)
        
        if not user:
            await ctx.send("❌ Benutzer nicht gefunden!")
            return
        
        # Send reply to user
        embed = discord.Embed(
            title="📬 Antwort vom Moderationsteam",
            description=message,
            color=0x3498DB,
            timestamp=datetime.now()
        )
        embed.set_footer(text=f"Geantwortet von {ctx.author.display_name}")
        
        try:
            await user.send(embed=embed)
            
            # Confirmation in modmail channel
            confirm_embed = discord.Embed(
                title="✅ Antwort gesendet",
                description=f"Nachricht an {user.mention} gesendet!",
                color=0x4CAF50
            )
            await ctx.send(embed=confirm_embed)
            
        except discord.Forbidden:
            await ctx.send("❌ Kann dem Benutzer keine DM senden! (DMs blockiert)")
    
    @commands.command(name='close')
    @has_role_permission(['admin', 'moderator'])
    async def close_modmail(self, ctx, *, reason="Kein Grund angegeben"):
        """Schließt ein ModMail Ticket"""
        # Check if this is a modmail channel
        async with aiosqlite.connect(self.db.db_path) as db:
            cursor = await db.execute(
                "SELECT user_id FROM modmail_threads WHERE channel_id = ? AND status = 'open'",
                (ctx.channel.id,)
            )
            result = await cursor.fetchone()
        
        if not result:
            await ctx.send("❌ Dies ist kein aktives ModMail Ticket!")
            return
        
        user_id = result[0]
        user = self.bot.get_user(user_id)
        
        # Update database
        async with aiosqlite.connect(self.db.db_path) as db:
            await db.execute(
                "UPDATE modmail_threads SET status = 'closed' WHERE channel_id = ?",
                (ctx.channel.id,)
            )
            await db.commit()
        
        # Send closure notification to user
        if user:
            try:
                embed = discord.Embed(
                    title="🔒 ModMail Ticket geschlossen",
                    description=f"Dein ModMail Ticket wurde geschlossen.\n\n"
                               f"**Grund:** {reason}\n"
                               f"**Geschlossen von:** {ctx.author.display_name}",
                    color=0xFF6B6B,
                    timestamp=datetime.now()
                )
                embed.set_footer(text="Du kannst jederzeit ein neues Ticket erstellen mit !modmail <nachricht>")
                await user.send(embed=embed)
            except discord.Forbidden:
                pass  # Can't send DM
        
        # Delete channel after delay
        embed = discord.Embed(
            title="🔒 Ticket wird geschlossen",
            description=f"Dieses Ticket wird in 10 Sekunden gelöscht...\n\n**Grund:** {reason}",
            color=0xFF6B6B
        )
        await ctx.send(embed=embed)
        
        await asyncio.sleep(10)
        await ctx.channel.delete(reason=f"ModMail geschlossen von {ctx.author}")
    
    @commands.Cog.listener()
    async def on_message(self, message):
        """Handle DM messages for modmail"""
        # Ignore bot messages
        if message.author.bot:
            return
        
        # Only handle DMs
        if message.guild:
            return
        
        # Check if user has an open modmail thread
        async with aiosqlite.connect(self.db.db_path) as db:
            cursor = await db.execute(
                "SELECT channel_id FROM modmail_threads WHERE user_id = ? AND status = 'open'",
                (message.author.id,)
            )
            result = await cursor.fetchone()
        
        if result:
            channel_id = result[0]
            channel = self.bot.get_channel(channel_id)
            
            if channel:
                # Forward message to modmail channel
                embed = discord.Embed(
                    title="💬 Neue Nachricht",
                    description=message.content,
                    color=0x3498DB,
                    timestamp=datetime.now()
                )
                embed.set_author(
                    name=f"{message.author.display_name} ({message.author})",
                    icon_url=message.author.avatar.url if message.author.avatar else message.author.default_avatar.url
                )
                
                await channel.send(embed=embed)
                
                # Handle attachments
                if message.attachments:
                    for attachment in message.attachments:
                        await channel.send(f"📎 **Anhang:** {attachment.url}")

async def setup(bot):
    await bot.add_cog(ModMail(bot))
