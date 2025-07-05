import discord
import json
from datetime import datetime, timedelta
import asyncio
import re

def load_config():
    """Load bot configuration"""
    with open('config.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def format_time_duration(seconds):
    """Format seconds into a readable time duration"""
    if seconds < 60:
        return f"{int(seconds)}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}m {secs}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours}h {minutes}m"

def format_number(number):
    """Format numbers with thousand separators"""
    return f"{number:,}".replace(",", ".")

def create_progress_bar(progress, length=10, filled_char="█", empty_char="░"):
    """Create a visual progress bar"""
    filled_length = int(length * progress / 100)
    bar = filled_char * filled_length + empty_char * (length - filled_length)
    return f"{bar} {progress:.1f}%"

def safe_member_mention(bot, user_id, fallback_name="Unbekannter Benutzer"):
    """Safely get a member mention or fallback to name"""
    user = bot.get_user(user_id)
    if user:
        return user.mention
    return f"{fallback_name} ({user_id})"

def safe_member_name(bot, user_id, fallback_name="Unbekannter Benutzer"):
    """Safely get a member name or fallback"""
    user = bot.get_user(user_id)
    if user:
        return user.display_name
    return f"{fallback_name}"

def truncate_text(text, max_length=1024, suffix="..."):
    """Truncate text to fit Discord embed limits"""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix

def create_embed_with_author(title, description, author, color=0x3498DB):
    """Create an embed with author information"""
    embed = discord.Embed(
        title=title,
        description=description,
        color=color,
        timestamp=datetime.now()
    )
    embed.set_author(
        name=author.display_name,
        icon_url=author.avatar.url if author.avatar else author.default_avatar.url
    )
    return embed

def create_success_embed(title, description, footer=None):
    """Create a success embed with green color"""
    embed = discord.Embed(
        title=f"✅ {title}",
        description=description,
        color=0x4CAF50,
        timestamp=datetime.now()
    )
    if footer:
        embed.set_footer(text=footer)
    return embed

def create_error_embed(title, description, footer=None):
    """Create an error embed with red color"""
    embed = discord.Embed(
        title=f"❌ {title}",
        description=description,
        color=0xFF6B6B,
        timestamp=datetime.now()
    )
    if footer:
        embed.set_footer(text=footer)
    return embed

def create_warning_embed(title, description, footer=None):
    """Create a warning embed with orange color"""
    embed = discord.Embed(
        title=f"⚠️ {title}",
        description=description,
        color=0xFF8C00,
        timestamp=datetime.now()
    )
    if footer:
        embed.set_footer(text=footer)
    return embed

def create_info_embed(title, description, footer=None):
    """Create an info embed with blue color"""
    embed = discord.Embed(
        title=f"ℹ️ {title}",
        description=description,
        color=0x3498DB,
        timestamp=datetime.now()
    )
    if footer:
        embed.set_footer(text=footer)
    return embed

async def send_temp_message(ctx, embed_or_content, delete_after=10):
    """Send a temporary message that auto-deletes"""
    if isinstance(embed_or_content, discord.Embed):
        message = await ctx.send(embed=embed_or_content)
    else:
        message = await ctx.send(embed_or_content)
    
    await asyncio.sleep(delete_after)
    try:
        await message.delete()
    except discord.NotFound:
        pass  # Message already deleted

def validate_channel_name(name):
    """Validate and sanitize channel name"""
    # Remove invalid characters
    name = re.sub(r'[^a-zA-Z0-9\-_äöüÄÖÜß ]', '', name)
    # Replace spaces with hyphens
    name = name.replace(' ', '-').lower()
    # Remove multiple consecutive hyphens
    name = re.sub(r'-+', '-', name)
    # Remove leading/trailing hyphens
    name = name.strip('-')
    
    # Ensure minimum length
    if len(name) < 2:
        name = "temp-channel"
    
    # Ensure maximum length (Discord limit is 100)
    if len(name) > 100:
        name = name[:100]
    
    return name

def parse_time_string(time_str):
    """
    Parse time strings like '1h', '30m', '2h30m' into seconds
    
    Args:
        time_str (str): Time string to parse
        
    Returns:
        int: Total seconds or None if invalid
    """
    time_str = time_str.lower().strip()
    
    # Pattern to match time components
    pattern = r'(?:(\d+)h)?(?:(\d+)m)?(?:(\d+)s)?'
    match = re.match(pattern, time_str)
    
    if not match:
        return None
    
    hours, minutes, seconds = match.groups()
    
    total_seconds = 0
    if hours:
        total_seconds += int(hours) * 3600
    if minutes:
        total_seconds += int(minutes) * 60
    if seconds:
        total_seconds += int(seconds)
    
    return total_seconds if total_seconds > 0 else None

def get_german_weekday(date):
    """Get German weekday name"""
    weekdays = [
        "Montag", "Dienstag", "Mittwoch", "Donnerstag",
        "Freitag", "Samstag", "Sonntag"
    ]
    return weekdays[date.weekday()]

def get_german_month(date):
    """Get German month name"""
    months = [
        "Januar", "Februar", "März", "April", "Mai", "Juni",
        "Juli", "August", "September", "Oktober", "November", "Dezember"
    ]
    return months[date.month - 1]

def format_german_date(date):
    """Format date in German format"""
    weekday = get_german_weekday(date)
    month = get_german_month(date)
    return f"{weekday}, {date.day}. {month} {date.year}"

def format_german_datetime(date):
    """Format datetime in German format"""
    weekday = get_german_weekday(date)
    month = get_german_month(date)
    return f"{weekday}, {date.day}. {month} {date.year} um {date.strftime('%H:%M')} Uhr"

def create_raid_embed_template():
    """Create a template embed for raids"""
    embed = discord.Embed(
        title="⚔️ Dune Awakening Raid",
        color=0xFF8C00,
        timestamp=datetime.now()
    )
    
    embed.add_field(
        name="🗡️ Kampfrollen",
        value="Wähle deine Rolle für den Raid",
        inline=False
    )
    
    embed.set_footer(text="Die Spice muss fließen! • Verwende die Reaktionen zur Anmeldung")
    
    return embed

def chunk_list(lst, chunk_size):
    """Split a list into chunks of specified size"""
    for i in range(0, len(lst), chunk_size):
        yield lst[i:i + chunk_size]

def get_emoji_for_role(role_name):
    """Get appropriate emoji for raid roles"""
    role_emojis = {
        "dps": "🗡️",
        "tank": "🛡️", 
        "healer": "❤️",
        "support": "❤️",
        "sniper": "🎯",
        "engineer": "🔧",
        "flex": "👥",
        "driver": "🚗",
        "fighter": "🔫",
        "collector": "⛏️",
        "scout": "👁️"
    }
    
    role_lower = role_name.lower()
    for key, emoji in role_emojis.items():
        if key in role_lower:
            return emoji
    
    return "👤"  # Default emoji

async def cleanup_old_messages(channel, older_than_days=7, limit=100):
    """Clean up old messages in a channel"""
    cutoff_date = datetime.now() - timedelta(days=older_than_days)
    
    deleted_count = 0
    async for message in channel.history(limit=limit):
        if message.created_at < cutoff_date:
            try:
                await message.delete()
                deleted_count += 1
                await asyncio.sleep(1)  # Rate limit protection
            except discord.NotFound:
                pass  # Message already deleted
            except discord.Forbidden:
                break  # No permission to delete
    
    return deleted_count

def is_valid_discord_id(user_input):
    """Check if input is a valid Discord ID"""
    try:
        user_id = int(user_input)
        # Discord IDs are typically 17-19 digits
        return 17 <= len(str(user_id)) <= 19
    except ValueError:
        return False

def extract_user_id(user_input):
    """Extract user ID from mention or direct ID"""
    # Remove mention formatting
    user_input = user_input.strip("<@!>")
    
    if is_valid_discord_id(user_input):
        return int(user_input)
    
    return None
