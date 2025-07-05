import discord
from discord.ext import commands
import json
from functools import wraps

def load_config():
    """Load configuration file"""
    with open('config.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def has_role_permission(required_roles, command_name=None):
    """
    Decorator to check if user has required roles
    
    Args:
        required_roles (list): Default list of role names that can use the command
        command_name (str): Optional command name to check custom permissions
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(self, ctx, *args, **kwargs):
            config = load_config()
            
            # Server owners and bot owners bypass all restrictions
            if ctx.author.id == ctx.guild.owner_id:
                return await func(self, ctx, *args, **kwargs)
            
            # Check for custom command permissions first
            custom_permissions = config.get('command_permissions', {})
            if command_name and command_name in custom_permissions:
                required_roles = custom_permissions[command_name]
            
            # Check if user has any of the required roles
            user_role_ids = [role.id for role in ctx.author.roles]
            
            for role_name in required_roles:
                role_id = config['roles'].get(role_name)
                if role_id and role_id in user_role_ids:
                    return await func(self, ctx, *args, **kwargs)
            
            # Create error embed
            embed = discord.Embed(
                title="❌ Keine Berechtigung",
                description=f"Du benötigst eine der folgenden Rollen um diesen Befehl zu verwenden:\n\n"
                           f"**Benötigte Rollen:**\n" + 
                           "\n".join([f"• {role_name.capitalize()}" for role_name in required_roles]),
                color=0xFF6B6B
            )
            embed.set_footer(text="Kontaktiere einen Administrator wenn du glaubst, dass dies ein Fehler ist.")
            
            await ctx.send(embed=embed)
            
        return wrapper
    return decorator

def is_bot_admin():
    """Check if user is a bot administrator"""
    def predicate(ctx):
        config = load_config()
        admin_role_id = config['roles'].get('admin')
        
        if ctx.author.id == ctx.guild.owner_id:
            return True
            
        if admin_role_id:
            return any(role.id == admin_role_id for role in ctx.author.roles)
        
        return False
    
    return commands.check(predicate)

def is_moderator_or_higher():
    """Check if user is a moderator or has higher permissions"""
    def predicate(ctx):
        config = load_config()
        
        if ctx.author.id == ctx.guild.owner_id:
            return True
        
        user_role_ids = [role.id for role in ctx.author.roles]
        
        # Check for admin or moderator roles
        for role_name in ['admin', 'moderator']:
            role_id = config['roles'].get(role_name)
            if role_id and role_id in user_role_ids:
                return True
                
        return False
    
    return commands.check(predicate)

def can_manage_raids():
    """Check if user can manage raids"""
    def predicate(ctx):
        config = load_config()
        
        if ctx.author.id == ctx.guild.owner_id:
            return True
        
        user_role_ids = [role.id for role in ctx.author.roles]
        
        # Check for admin, moderator, or raid_leader roles
        for role_name in ['admin', 'moderator', 'raid_leader']:
            role_id = config['roles'].get(role_name)
            if role_id and role_id in user_role_ids:
                return True
                
        return False
    
    return commands.check(predicate)

async def send_permission_error(ctx, required_roles):
    """Send a formatted permission error message"""
    embed = discord.Embed(
        title="❌ Zugriff verweigert",
        description="Du hast nicht die erforderlichen Berechtigungen für diesen Befehl.",
        color=0xFF6B6B
    )
    
    if required_roles:
        role_list = "\n".join([f"• {role.capitalize()}" for role in required_roles])
        embed.add_field(
            name="Benötigte Rollen",
            value=role_list,
            inline=False
        )
    
    embed.set_footer(text="Kontaktiere einen Administrator bei Fragen.")
    await ctx.send(embed=embed)

def get_user_permission_level(member, config):
    """
    Get the permission level of a user
    
    Returns:
        str: Permission level ('owner', 'admin', 'moderator', 'raid_leader', 'member', 'rekrut', 'none')
    """
    if member.id == member.guild.owner_id:
        return 'owner'
    
    user_role_ids = [role.id for role in member.roles]
    
    # Check in order of hierarchy
    permission_hierarchy = ['admin', 'moderator', 'raid_leader', 'member', 'rekrut']
    
    for role_name in permission_hierarchy:
        role_id = config['roles'].get(role_name)
        if role_id and role_id in user_role_ids:
            return role_name
    
    return 'none'

def format_permission_error(required_permissions, user_permission):
    """Format a detailed permission error message"""
    embed = discord.Embed(
        title="🚫 Berechtigung erforderlich",
        color=0xFF6B6B
    )
    
    embed.add_field(
        name="Deine Berechtigung",
        value=f"**{user_permission.capitalize()}**",
        inline=True
    )
    
    embed.add_field(
        name="Erforderlich",
        value=f"**{' oder '.join(required_permissions).title()}**",
        inline=True
    )
    
    embed.add_field(
        name="💡 Tipp",
        value="Kontaktiere einen Administrator oder Moderator für Hilfe.",
        inline=False
    )
    
    return embed

def check_command_permission(user, command_name, default_roles):
    """
    Check if user has permission for a specific command
    
    Args:
        user: Discord member object
        command_name: Name of the command
        default_roles: Default required roles if no custom config exists
        
    Returns:
        bool: True if user has permission, False otherwise
    """
    config = load_config()
    
    # Server owners bypass all restrictions
    if user.id == user.guild.owner_id:
        return True
    
    # Check for custom command permissions
    custom_permissions = config.get('command_permissions', {})
    required_roles = custom_permissions.get(command_name, default_roles)
    
    # Check if user has any of the required roles
    user_role_ids = [role.id for role in user.roles]
    
    for role_name in required_roles:
        role_id = config['roles'].get(role_name)
        if role_id and role_id in user_role_ids:
            return True
    
    return False
