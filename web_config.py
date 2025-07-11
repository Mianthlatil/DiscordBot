
from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
import json
import os
import discord
from discord.ext import commands
import asyncio
import threading
from functools import wraps
import traceback

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'your-secret-key-here')

# Global bot instance
bot_instance = None

def load_config():
    """Load configuration from JSON file"""
    try:
        with open('config.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_config(config):
    """Save configuration to JSON file"""
    with open('config.json', 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=4, ensure_ascii=False)

def get_discord_guilds():
    """Get all Discord guilds the bot is connected to"""
    try:
        # Try to get guilds from existing bot instance
        try:
            import sys
            import importlib
            
            # Reload main module to ensure we get the latest bot instance
            if 'main' in sys.modules:
                importlib.reload(sys.modules['main'])
            
            import main
            
            print(f"Bot instance available: {hasattr(main, 'bot')}")
            if hasattr(main, 'bot') and main.bot:
                print(f"Bot is ready: {main.bot.is_ready()}")
                print(f"Bot user: {main.bot.user}")
                
                if main.bot.is_ready():
                    guilds = []
                    for guild in main.bot.guilds:
                        guilds.append({
                            'id': guild.id,
                            'name': guild.name,
                            'icon': str(guild.icon) if guild.icon else None,
                            'member_count': guild.member_count
                        })
                    print(f"Found {len(guilds)} guilds: {[g['name'] for g in guilds]}")
                    return guilds
                else:
                    print("Bot is not ready yet - waiting for connection...")
                    return []
            else:
                print("Bot instance not found or not available")
        except ImportError as e:
            print(f"Import error: {e}")
        except Exception as e:
            print(f"Bot access error: {e}")
            import traceback
            traceback.print_exc()
        
        return []
    except Exception as e:
        print(f"Error fetching Discord guilds: {e}")
        import traceback
        traceback.print_exc()
        return []

def get_discord_roles(guild_id=None):
    """Get Discord roles from the bot instance"""
    try:
        config = load_config()
        target_guild_id = guild_id or session.get('selected_guild_id') or config.get('guild_id')
        
        if not target_guild_id:
            print("No guild ID provided")
            return []
        
        # Try to get roles from existing bot instance
        try:
            import sys
            import importlib
            
            # Reload main module to ensure we get the latest bot instance
            if 'main' in sys.modules:
                importlib.reload(sys.modules['main'])
            
            import main
            
            if hasattr(main, 'bot') and main.bot and main.bot.is_ready():
                guild = main.bot.get_guild(int(target_guild_id))
                if guild:
                    roles = [{'id': role.id, 'name': role.name, 'color': str(role.color)} 
                           for role in guild.roles if role.name != '@everyone' and not role.managed]
                    print(f"Found {len(roles)} roles for guild {guild.name}")
                    return roles
                else:
                    print(f"Guild with ID {target_guild_id} not found")
            else:
                print("Bot is not ready or not available for roles")
        except ImportError as e:
            print(f"Import error for roles: {e}")
        except Exception as e:
            print(f"Bot access error for roles: {e}")
            import traceback
            traceback.print_exc()
        
        return []
    except Exception as e:
        print(f"Error fetching Discord roles: {e}")
        import traceback
        traceback.print_exc()
        return []

def get_discord_channels(guild_id=None):
    """Get Discord channels from the bot instance"""
    try:
        config = load_config()
        target_guild_id = guild_id or session.get('selected_guild_id') or config.get('guild_id')
        
        if not target_guild_id:
            print("No guild ID provided for channels")
            return []
        
        # Try to get channels from existing bot instance
        try:
            import sys
            import importlib
            
            # Reload main module to ensure we get the latest bot instance
            if 'main' in sys.modules:
                importlib.reload(sys.modules['main'])
            
            import main
            
            if hasattr(main, 'bot') and main.bot and main.bot.is_ready():
                guild = main.bot.get_guild(int(target_guild_id))
                if guild:
                    channels = []
                    for channel in guild.channels:
                        if hasattr(channel, 'type'):
                            channel_type = str(channel.type).replace('ChannelType.', '')
                            channels.append({
                                'id': channel.id, 
                                'name': channel.name, 
                                'type': channel_type,
                                'category': channel.category.name if channel.category else None
                            })
                    print(f"Found {len(channels)} channels for guild {guild.name}")
                    return channels
                else:
                    print(f"Guild with ID {target_guild_id} not found for channels")
            else:
                print("Bot is not ready or not available for channels")
        except ImportError as e:
            print(f"Import error for channels: {e}")
        except Exception as e:
            print(f"Bot access error for channels: {e}")
            import traceback
            traceback.print_exc()
        
        return []
    except Exception as e:
        print(f"Error fetching Discord channels: {e}")
        import traceback
        traceback.print_exc()
        return []

def require_auth(f):
    """Decorator to require authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'authenticated' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def require_guild_selection(f):
    """Decorator to require guild selection before accessing settings"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'authenticated' not in session:
            return redirect(url_for('login'))
        
        selected_guild_id = session.get('selected_guild_id')
        if not selected_guild_id:
            flash('Bitte wähle zuerst einen Discord Server aus!', 'warning')
            return redirect(url_for('index'))
        
        # Verify guild still exists
        guilds = get_discord_guilds()
        if not any(g['id'] == int(selected_guild_id) for g in guilds):
            session.pop('selected_guild_id', None)
            flash('Der ausgewählte Server ist nicht mehr verfügbar!', 'error')
            return redirect(url_for('index'))
        
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    """Main dashboard"""
    if 'authenticated' not in session:
        return redirect(url_for('login'))
    
    config = load_config()
    guilds = get_discord_guilds()
    selected_guild_id = session.get('selected_guild_id')
    
    # If no guild selected, show guild selection page
    if not selected_guild_id:
        return render_template('guild_selection.html', guilds=guilds)
    
    # Get selected guild info
    selected_guild = next((g for g in guilds if g['id'] == int(selected_guild_id)), None)
    
    # If selected guild not found, reset selection
    if not selected_guild:
        session.pop('selected_guild_id', None)
        return render_template('guild_selection.html', guilds=guilds)
    
    return render_template('dashboard.html', 
                         config=config, 
                         guilds=guilds,
                         selected_guild=selected_guild,
                         selected_guild_id=selected_guild_id)

@app.route('/select_guild', methods=['POST'])
@require_auth
def select_guild():
    """Select a Discord guild to manage"""
    guild_id = request.form.get('guild_id')
    
    if guild_id:
        try:
            guilds = get_discord_guilds()
            if any(g['id'] == int(guild_id) for g in guilds):
                session['selected_guild_id'] = int(guild_id)
                guild_name = next(g['name'] for g in guilds if g['id'] == int(guild_id))
                flash(f'Discord Server "{guild_name}" ausgewählt!', 'success')
            else:
                flash('Server nicht gefunden!', 'error')
        except ValueError:
            flash('Ungültige Server ID!', 'error')
    
    return redirect(url_for('index'))

@app.route('/change_guild')
@require_auth
def change_guild():
    """Change the selected guild"""
    session.pop('selected_guild_id', None)
    flash('Server-Auswahl zurückgesetzt. Bitte wähle einen neuen Server.', 'info')
    return redirect(url_for('index'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Simple login page"""
    if request.method == 'POST':
        password = request.form.get('password')
        # In production, use a secure password hash
        if password == os.environ.get('ADMIN_PASSWORD', 'admin123'):
            session['authenticated'] = True
            flash('Erfolgreich angemeldet!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Falsches Passwort!', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """Logout and clear session"""
    session.clear()
    flash('Erfolgreich abgemeldet!', 'info')
    return redirect(url_for('login'))

@app.route('/basic_settings', methods=['GET', 'POST'])
@require_guild_selection
def basic_settings():
    """Basic bot settings"""
    config = load_config()
    
    if request.method == 'POST':
        config['prefix'] = request.form.get('prefix', '!')
        guild_id = request.form.get('guild_id')
        if guild_id:
            try:
                config['guild_id'] = int(guild_id)
            except ValueError:
                flash('Ungültige Guild ID!', 'error')
                return render_template('basic_settings.html', config=config)
        
        save_config(config)
        flash('Grundeinstellungen gespeichert!', 'success')
        return redirect(url_for('index'))
    
    return render_template('basic_settings.html', config=config)

@app.route('/roles', methods=['GET', 'POST'])
@require_guild_selection
def roles():
    """Role configuration"""
    config = load_config()
    
    if request.method == 'POST':
        # Handle Discord roles directly
        role_names = request.form.getlist('role_names[]')
        role_ids = request.form.getlist('role_ids[]')
        
        if 'roles' not in config:
            config['roles'] = {}
        
        # Clear existing roles
        config['roles'] = {}
        
        # Update with selected Discord roles
        for name, role_id in zip(role_names, role_ids):
            if name.strip() and role_id:
                try:
                    config['roles'][name.strip()] = int(role_id)
                except ValueError:
                    flash(f'Ungültige ID für Rolle {name}!', 'error')
                    return render_template('roles.html', config=config)
        
        save_config(config)
        flash('Rollen-Konfiguration gespeichert!', 'success')
        return redirect(url_for('index'))
    
    return render_template('roles.html', config=config)

@app.route('/channels', methods=['GET', 'POST'])
@require_guild_selection
def channels():
    """Channel configuration"""
    config = load_config()
    
    if request.method == 'POST':
        if 'channels' not in config:
            config['channels'] = {}
        
        for channel_name in ['modmail_category', 'temp_voice_category', 'raid_announcements']:
            channel_id = request.form.get(f'channel_{channel_name}')
            if channel_id:
                try:
                    config['channels'][channel_name] = int(channel_id)
                except ValueError:
                    flash(f'Ungültige ID für {channel_name}!', 'error')
                    return render_template('channels.html', config=config)
        
        save_config(config)
        flash('Kanal-Konfiguration gespeichert!', 'success')
        return redirect(url_for('index'))
    
    return render_template('channels.html', config=config)

@app.route('/permissions')
@require_guild_selection
def permissions():
    """Command permissions overview"""
    config = load_config()
    
    # Alle verfügbaren Commands
    all_commands = [
        "balance", "leaderboard", "give", "take",
        "event", "event-edit", "event_info", "crawler", "carrier",
        "lockvoice", "unlockvoice", "ragelock", "moveall", "voice_stats",
        "temp_voice", "temp_limit", "temp_name", "temp_kick",
        "createraid", "anmelden", "raid_info", "spice_crawl",
        "modmail", "reply", "close", "force_promote", "setup"
    ]
    
    command_permissions = config.get('command_permissions', {})
    configured_roles = config.get('roles', {})
    
    return render_template('permissions.html', 
                         config=config, 
                         all_commands=all_commands,
                         command_permissions=command_permissions,
                         configured_roles=configured_roles)

@app.route('/update_permission', methods=['POST'])
@require_guild_selection
def update_permission():
    """Update individual command permission"""
    config = load_config()
    
    command = request.form.get('command')
    selected_roles = request.form.getlist('roles')
    
    if not command:
        return jsonify({'error': 'Command ist erforderlich'}), 400
    
    if 'command_permissions' not in config:
        config['command_permissions'] = {}
    
    # Allow empty role list to remove all permissions
    config['command_permissions'][command] = selected_roles
    save_config(config)
    
    return jsonify({'success': True, 'message': f'Berechtigungen für {command} aktualisiert'})

@app.route('/voice_promotion', methods=['GET', 'POST'])
@require_guild_selection
def voice_promotion():
    """Voice promotion settings"""
    config = load_config()
    
    if request.method == 'POST':
        if 'voice_promotion' not in config:
            config['voice_promotion'] = {}
        
        try:
            config['voice_promotion']['hours_required'] = int(request.form.get('hours_required', 24))
            config['voice_promotion']['check_interval'] = int(request.form.get('check_interval', 300))
        except ValueError:
            flash('Ungültige Zahlenwerte!', 'error')
            return render_template('voice_promotion.html', config=config)
        
        save_config(config)
        flash('Voice Promotion Einstellungen gespeichert!', 'success')
        return redirect(url_for('index'))
    
    return render_template('voice_promotion.html', config=config)

@app.route('/temp_voice', methods=['GET', 'POST'])
@require_guild_selection
def temp_voice():
    """Temporary voice settings"""
    config = load_config()
    
    if request.method == 'POST':
        if 'temp_voice' not in config:
            config['temp_voice'] = {}
        
        config['temp_voice']['default_name'] = request.form.get('default_name', "{user}'s Channel")
        
        try:
            config['temp_voice']['default_limit'] = int(request.form.get('default_limit', 100))
        except ValueError:
            flash('Ungültiger Zahlenwert für Limit!', 'error')
            return render_template('temp_voice.html', config=config)
        
        save_config(config)
        flash('Temp Voice Einstellungen gespeichert!', 'success')
        return redirect(url_for('index'))
    
    return render_template('temp_voice.html', config=config)

@app.route('/api/config')
@require_auth
def api_config():
    """API endpoint to get current config"""
    return jsonify(load_config())

@app.route('/api/discord_roles')
@require_auth
def api_discord_roles():
    """API endpoint to get Discord roles"""
    guild_id = request.args.get('guild_id')
    roles = get_discord_roles(guild_id)
    return jsonify(roles)

@app.route('/api/discord_channels')
@require_auth
def api_discord_channels():
    """API endpoint to get Discord channels"""
    guild_id = request.args.get('guild_id')
    channels = get_discord_channels(guild_id)
    return jsonify(channels)

@app.route('/api/discord_guilds')
@require_auth
def api_discord_guilds():
    """API endpoint to get Discord guilds"""
    guilds = get_discord_guilds()
    return jsonify(guilds)

@app.route('/reset_permissions', methods=['POST'])
@require_guild_selection
def reset_permissions():
    """Reset all command permissions"""
    config = load_config()
    config['command_permissions'] = {}
    save_config(config)
    flash('Alle Berechtigungen wurden zurückgesetzt!', 'success')
    return redirect(url_for('permissions'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
