import discord
from discord.ext import commands
import json
from datetime import datetime, timedelta
from database import Database
from utils.permissions import has_role_permission

class EventSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = Database()
        
        # Load config
        with open('config.json', 'r', encoding='utf-8') as f:
            self.config = json.load(f)
        
        # Event roles mapping
        self.event_roles = {
            '🗡️': 'Attack',
            '🛡️': 'Def', 
            '⛏️': 'Crawler',
            '📦': 'Carrier'
        }
    
    @commands.command(name='event', aliases=['create_event'])
    @has_role_permission(['admin', 'moderator'])
    async def create_event(self, ctx, *, description):
        """Erstellt ein neues Event mit Anmeldungssystem"""
        # Generate unique event ID
        event_id = f"event_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        embed = discord.Embed(
            title="⚔️ Dune Awakening Event",
            description=description,
            color=0xFF8C00,
            timestamp=datetime.now()
        )
        
        embed.add_field(
            name="📝 Anmeldung per Reaktion",
            value="🗡️ - **Attack** (Angreifer)\n"
                  "🛡️ - **Def** (Verteidiger)\n"
                  "⛏️ - **Crawler** (nur Moderatoren)\n"
                  "📦 - **Carrier** (nur Moderatoren)",
            inline=False
        )
        
        embed.add_field(
            name="ℹ️ Event-ID",
            value=f"`{event_id}`",
            inline=True
        )
        
        embed.add_field(
            name="👤 Erstellt von",
            value=ctx.author.mention,
            inline=True
        )
        
        embed.add_field(
            name="📊 Anmeldungen",
            value="🗡️ Attack: 0\n🛡️ Def: 0\n⛏️ Crawler: 0\n📦 Carrier: 0",
            inline=False
        )
        
        embed.set_footer(text=f"Event-ID: {event_id} | Verwende !event_info <ID> für Details")
        
        message = await ctx.send(embed=embed)
        
        # Add reaction buttons
        reactions = ['🗡️', '🛡️', '⛏️', '📦']
        for reaction in reactions:
            await message.add_reaction(reaction)
        
        # Store event info in database
        await self.store_event(event_id, ctx.author.id, description, message.id, ctx.channel.id)
        
        await ctx.send(f"✅ Event erstellt! ID: `{event_id}`")
    
    @commands.command(name='event_info', aliases=['eventinfo'])
    async def event_info(self, ctx, event_id: str):
        """Zeigt Event-Anmeldungen an"""
        registrations = await self.get_event_registrations(event_id)
        
        if not registrations:
            await ctx.send(f"❌ Keine Anmeldungen für Event `{event_id}` gefunden!")
            return
        
        embed = discord.Embed(
            title=f"⚔️ Event Anmeldungen: {event_id}",
            color=0xFF8C00,
            timestamp=datetime.now()
        )
        
        # Group by role
        role_groups = {
            'Attack': [],
            'Def': [],
            'Crawler': [],
            'Carrier': []
        }
        
        for user_id, username, role, registered_at in registrations:
            if role in role_groups:
                role_groups[role].append((username, registered_at))
        
        # Display each role group
        role_emojis = {'Attack': '🗡️', 'Def': '🛡️', 'Crawler': '⛏️', 'Carrier': '📦'}
        
        for role, members in role_groups.items():
            emoji = role_emojis[role]
            if members:
                member_list = []
                for i, (username, registered_at) in enumerate(members, 1):
                    member_list.append(f"{i}. **{username}**")
                
                embed.add_field(
                    name=f"{emoji} {role} ({len(members)})",
                    value="\n".join(member_list),
                    inline=True
                )
            else:
                embed.add_field(
                    name=f"{emoji} {role} (0)",
                    value="Niemand angemeldet",
                    inline=True
                )
        
        total_registrations = len(list(registrations))
        embed.set_footer(text=f"Gesamt: {total_registrations} Spieler angemeldet")
        await ctx.send(embed=embed)
    
    @commands.command(name='assign_crawler', aliases=['crawler'])
    @has_role_permission(['admin', 'moderator'])
    async def assign_crawler(self, ctx, event_id: str, member: discord.Member):
        """Meldet einen Spieler als Crawler an (nur Moderatoren)"""
        success = await self.register_for_event(event_id, member.id, member.display_name, 'Crawler')
        
        if success:
            embed = discord.Embed(
                title="⛏️ Als Crawler angemeldet",
                description=f"**{member.display_name}** wurde als **Crawler** für Event `{event_id}` angemeldet!",
                color=0x4CAF50
            )
            embed.set_footer(text=f"Angemeldet von {ctx.author.display_name}")
        else:
            embed = discord.Embed(
                title="❌ Bereits angemeldet",
                description=f"**{member.display_name}** ist bereits für Event `{event_id}` angemeldet!",
                color=0xFF6B6B
            )
        
        await ctx.send(embed=embed)
        await self.update_event_message(event_id)
    
    @commands.command(name='assign_carrier', aliases=['carrier'])
    @has_role_permission(['admin', 'moderator'])
    async def assign_carrier(self, ctx, event_id: str, member: discord.Member):
        """Meldet einen Spieler als Carrier an (nur Moderatoren)"""
        success = await self.register_for_event(event_id, member.id, member.display_name, 'Carrier')
        
        if success:
            embed = discord.Embed(
                title="📦 Als Carrier angemeldet",
                description=f"**{member.display_name}** wurde als **Carrier** für Event `{event_id}` angemeldet!",
                color=0x4CAF50
            )
            embed.set_footer(text=f"Angemeldet von {ctx.author.display_name}")
        else:
            embed = discord.Embed(
                title="❌ Bereits angemeldet",
                description=f"**{member.display_name}** ist bereits für Event `{event_id}` angemeldet!",
                color=0xFF6B6B
            )
        
        await ctx.send(embed=embed)
        await self.update_event_message(event_id)
    
    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        """Handle event registration reactions"""
        if user.bot:
            return
        
        # Check if this is an event message
        message = reaction.message
        if not message.embeds or "Event-ID:" not in message.embeds[0].footer.text:
            return
        
        # Extract event ID from footer
        footer_text = message.embeds[0].footer.text
        event_id = footer_text.split("Event-ID: ")[1].split(" |")[0]
        
        if str(reaction.emoji) in self.event_roles:
            role = self.event_roles[str(reaction.emoji)]
            
            # Check if user is moderator for special roles
            if role in ['Crawler', 'Carrier']:
                user_role_ids = [role.id for role in user.roles]
                mod_roles = ['admin', 'moderator']
                has_permission = False
                
                for mod_role in mod_roles:
                    role_id = self.config['roles'].get(mod_role)
                    if role_id and role_id in user_role_ids:
                        has_permission = True
                        break
                
                if not has_permission and user.id != message.guild.owner_id:
                    # Remove reaction and send error
                    await reaction.remove(user)
                    try:
                        embed = discord.Embed(
                            title="❌ Keine Berechtigung",
                            description=f"Nur Moderatoren können sich als **{role}** anmelden!",
                            color=0xFF6B6B
                        )
                        await user.send(embed=embed)
                    except discord.Forbidden:
                        pass
                    return
            
            # Register user for event
            success = await self.register_for_event(event_id, user.id, user.display_name, role)
            
            if success:
                try:
                    embed = discord.Embed(
                        title="✅ Erfolgreich angemeldet!",
                        description=f"Du wurdest als **{role}** für das Event angemeldet!",
                        color=0x4CAF50
                    )
                    await user.send(embed=embed)
                except discord.Forbidden:
                    pass
                
                # Update the event message
                await self.update_event_message(event_id)
            else:
                # Remove reaction if already registered
                await reaction.remove(user)
                try:
                    embed = discord.Embed(
                        title="❌ Bereits angemeldet",
                        description=f"Du bist bereits für dieses Event angemeldet!",
                        color=0xFF6B6B
                    )
                    await user.send(embed=embed)
                except discord.Forbidden:
                    pass
    
    async def store_event(self, event_id, creator_id, description, message_id, channel_id):
        """Store event information in database"""
        import aiosqlite
        async with aiosqlite.connect(self.db.db_path) as db:
            await db.execute('''
                CREATE TABLE IF NOT EXISTS events (
                    event_id TEXT PRIMARY KEY,
                    creator_id INTEGER,
                    description TEXT,
                    message_id INTEGER,
                    channel_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            await db.execute('''
                INSERT INTO events (event_id, creator_id, description, message_id, channel_id)
                VALUES (?, ?, ?, ?, ?)
            ''', (event_id, creator_id, description, message_id, channel_id))
            await db.commit()
    
    async def register_for_event(self, event_id, user_id, username, role):
        """Register user for an event"""
        import aiosqlite
        async with aiosqlite.connect(self.db.db_path) as db:
            await db.execute('''
                CREATE TABLE IF NOT EXISTS event_registrations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id TEXT,
                    user_id INTEGER,
                    username TEXT,
                    role TEXT,
                    registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(event_id, user_id)
                )
            ''')
            
            try:
                await db.execute('''
                    INSERT INTO event_registrations (event_id, user_id, username, role)
                    VALUES (?, ?, ?, ?)
                ''', (event_id, user_id, username, role))
                await db.commit()
                return True
            except Exception:
                return False  # Already registered
    
    async def get_event_registrations(self, event_id):
        """Get all registrations for an event"""
        import aiosqlite
        async with aiosqlite.connect(self.db.db_path) as db:
            cursor = await db.execute('''
                SELECT user_id, username, role, registered_at 
                FROM event_registrations 
                WHERE event_id = ?
                ORDER BY registered_at
            ''', (event_id,))
            return await cursor.fetchall()
    
    async def update_event_message(self, event_id):
        """Update the event message with current registrations"""
        try:
            # Get event info
            import aiosqlite
            async with aiosqlite.connect(self.db.db_path) as db:
                cursor = await db.execute(
                    "SELECT message_id, channel_id, description FROM events WHERE event_id = ?",
                    (event_id,)
                )
                result = await cursor.fetchone()
            
            if not result:
                return
            
            message_id, channel_id, description = result
            channel = self.bot.get_channel(channel_id)
            if not channel:
                return
            
            try:
                message = await channel.fetch_message(message_id)
            except discord.NotFound:
                return
            
            # Get current registrations
            registrations = await self.get_event_registrations(event_id)
            
            # Count by role
            role_counts = {'Attack': 0, 'Def': 0, 'Crawler': 0, 'Carrier': 0}
            for user_id, username, role, registered_at in registrations:
                if role in role_counts:
                    role_counts[role] += 1
            
            # Update embed
            embed = message.embeds[0]
            
            # Find and update the registration field
            for i, field in enumerate(embed.fields):
                if field.name == "📊 Anmeldungen":
                    embed.set_field_at(
                        i,
                        name="📊 Anmeldungen",
                        value=f"🗡️ Attack: {role_counts['Attack']}\n"
                              f"🛡️ Def: {role_counts['Def']}\n"
                              f"⛏️ Crawler: {role_counts['Crawler']}\n"
                              f"📦 Carrier: {role_counts['Carrier']}",
                        inline=False
                    )
                    break
            
            await message.edit(embed=embed)
            
        except Exception as e:
            print(f"Error updating event message: {e}")

async def setup(bot):
    await bot.add_cog(EventSystem(bot))