import discord
from discord.ext import commands
from discord import app_commands
import json
import aiosqlite
from datetime import datetime, timedelta
from database import Database
from utils.permissions import has_role_permission

class Economy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = Database()
        
        # Load config
        with open('config.json', 'r', encoding='utf-8') as f:
            self.config = json.load(f)
    
    @commands.command(name='balance', aliases=['bal', 'guthaben'])
    async def balance(self, ctx, member: discord.Member = None):
        """Zeigt das Guthaben eines Benutzers an"""
        target = member or ctx.author
        balance = await self.db.get_user_balance(target.id)
        
        embed = discord.Embed(
            title="💰 Spice Guthaben",
            description=f"**{target.display_name}** hat **{balance:,}** Spice",
            color=0xD4AF37
        )
        embed.set_thumbnail(url=target.avatar.url if target.avatar else target.default_avatar.url)
        await ctx.send(embed=embed)
    
    @app_commands.command(name="balance", description="Zeigt das Spice-Guthaben an")
    async def balance_slash(self, interaction: discord.Interaction, member: discord.Member = None):
        """Slash command version of balance"""
        target = member or interaction.user
        balance = await self.db.get_user_balance(target.id)
        
        embed = discord.Embed(
            title="💰 Spice Guthaben",
            description=f"**{target.display_name}** hat **{balance:,}** Spice",
            color=0xD4AF37
        )
        embed.set_thumbnail(url=target.avatar.url if target.avatar else target.default_avatar.url)
        await interaction.response.send_message(embed=embed)
    

    

    
    @commands.command(name='give', aliases=['geben'])
    @has_role_permission(['admin', 'moderator'])
    async def give_spice(self, ctx, member: discord.Member, amount: int):
        """Gibt einem Benutzer Spice (Nur für Moderatoren)"""
        if amount <= 0:
            await ctx.send("❌ Der Betrag muss positiv sein!")
            return
        
        await self.db.update_user_balance(member.id, amount)
        
        embed = discord.Embed(
            title="💰 Spice übertragen",
            description=f"**{member.display_name}** hat **{amount:,}** Spice erhalten!",
            color=0x4CAF50
        )
        embed.set_footer(text=f"Übertragen von {ctx.author.display_name}")
        await ctx.send(embed=embed)
    
    @commands.command(name='take', aliases=['nehmen'])
    @has_role_permission(['admin', 'moderator'])
    async def take_spice(self, ctx, member: discord.Member, amount: int):
        """Nimmt einem Benutzer Spice weg (Nur für Moderatoren)"""
        if amount <= 0:
            await ctx.send("❌ Der Betrag muss positiv sein!")
            return
        
        current_balance = await self.db.get_user_balance(member.id)
        if current_balance < amount:
            await ctx.send(f"❌ {member.display_name} hat nur {current_balance:,} Spice!")
            return
        
        await self.db.update_user_balance(member.id, -amount)
        
        embed = discord.Embed(
            title="💸 Spice abgezogen",
            description=f"**{amount:,}** Spice wurde von **{member.display_name}** abgezogen!",
            color=0xFF6B6B
        )
        embed.set_footer(text=f"Abgezogen von {ctx.author.display_name}")
        await ctx.send(embed=embed)
    
    @commands.command(name='leaderboard', aliases=['top', 'rangliste'])
    async def leaderboard(self, ctx):
        """Zeigt die Spice-Rangliste an"""
        async with aiosqlite.connect(self.db.db_path) as db:
            cursor = await db.execute('''
                SELECT user_id, balance FROM economy 
                WHERE balance > 0 
                ORDER BY balance DESC 
                LIMIT 10
            ''')
            results = await cursor.fetchall()
        
        if not results:
            await ctx.send("❌ Noch keine Daten für die Rangliste vorhanden!")
            return
        
        embed = discord.Embed(
            title="🏆 Spice Rangliste",
            description="Die reichsten Mitglieder der Gilde:",
            color=0xD4AF37
        )
        
        for i, (user_id, balance) in enumerate(results, 1):
            user = self.bot.get_user(user_id)
            username = user.display_name if user else f"Unbekannter Benutzer ({user_id})"
            
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
            embed.add_field(
                name=f"{medal} {username}",
                value=f"**{balance:,}** Spice",
                inline=False
            )
        
        await ctx.send(embed=embed)
    
    @app_commands.command(name="give-spice", description="Gibt einem Benutzer Spice (Nur für Moderatoren)")
    @app_commands.describe(member="Der Benutzer der Spice erhalten soll", amount="Die Menge an Spice")
    async def give_spice_slash(self, interaction: discord.Interaction, member: discord.Member, amount: int):
        """Slash command version of give_spice"""
        if not any(role.name.lower() in ['moderator', 'admin'] for role in interaction.user.roles):
            await interaction.response.send_message("❌ Du hast keine Berechtigung für diesen Befehl!", ephemeral=True)
            return
        
        if amount <= 0:
            await interaction.response.send_message("❌ Der Betrag muss positiv sein!", ephemeral=True)
            return
        
        await self.db.update_user_balance(member.id, amount)
        
        embed = discord.Embed(
            title="💰 Spice übertragen",
            description=f"**{member.display_name}** hat **{amount:,}** Spice erhalten!",
            color=0x4CAF50
        )
        embed.set_footer(text=f"Übertragen von {interaction.user.display_name}")
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="take-spice", description="Nimmt einem Benutzer Spice weg (Nur für Moderatoren)")
    @app_commands.describe(member="Der Benutzer dem Spice weggenommen werden soll", amount="Die Menge an Spice")
    async def take_spice_slash(self, interaction: discord.Interaction, member: discord.Member, amount: int):
        """Slash command version of take_spice"""
        if not any(role.name.lower() in ['moderator', 'admin'] for role in interaction.user.roles):
            await interaction.response.send_message("❌ Du hast keine Berechtigung für diesen Befehl!", ephemeral=True)
            return
        
        if amount <= 0:
            await interaction.response.send_message("❌ Der Betrag muss positiv sein!", ephemeral=True)
            return
        
        current_balance = await self.db.get_user_balance(member.id)
        if current_balance < amount:
            await interaction.response.send_message(f"❌ {member.display_name} hat nur {current_balance:,} Spice!", ephemeral=True)
            return
        
        await self.db.update_user_balance(member.id, -amount)
        
        embed = discord.Embed(
            title="💸 Spice abgezogen",
            description=f"**{amount:,}** Spice wurden von **{member.display_name}** abgezogen!",
            color=0xF44336
        )
        embed.set_footer(text=f"Abgezogen von {interaction.user.display_name}")
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="leaderboard", description="Zeigt die Spice-Rangliste an")
    async def leaderboard_slash(self, interaction: discord.Interaction):
        """Slash command version of leaderboard"""
        await interaction.response.defer()
        
        async with aiosqlite.connect(self.db.db_path) as db:
            cursor = await db.execute('''
                SELECT user_id, balance FROM economy 
                ORDER BY balance DESC 
                LIMIT 10
            ''')
            top_users = await cursor.fetchall()
        
        if not top_users:
            embed = discord.Embed(
                title="📊 Spice Rangliste",
                description="Noch keine Daten verfügbar!",
                color=0x3498DB
            )
            await interaction.followup.send(embed=embed)
            return
        
        embed = discord.Embed(
            title="📊 Spice Rangliste - Top 10",
            description="Die reichsten Mitglieder unseres Hauses:",
            color=0xFFD700
        )
        
        for i, (user_id, balance) in enumerate(top_users[:10], 1):
            user = self.bot.get_user(user_id)
            username = user.display_name if user else f"Unbekannter Benutzer"
            
            # Medal emojis for top 3
            if i == 1:
                medal = "🥇"
            elif i == 2:
                medal = "🥈" 
            elif i == 3:
                medal = "🥉"
            else:
                medal = f"{i}."
            
            embed.add_field(
                name=f"{medal} {username}",
                value=f"**{balance:,}** Spice",
                inline=False
            )
        
        await interaction.followup.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Economy(bot))
