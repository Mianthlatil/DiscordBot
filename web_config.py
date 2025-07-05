
from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
import json
import os
import discord
from discord.ext import commands
import asyncio
import threading
from functools import wraps

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

def require_auth(f):
    """Decorator to require authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'authenticated' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    """Main dashboard"""
    if 'authenticated' not in session:
        return redirect(url_for('login'))
    
    config = load_config()
    return render_template('dashboard.html', config=config)

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
@require_auth
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
@require_auth
def roles():
    """Role configuration"""
    config = load_config()
    
    if request.method == 'POST':
        if 'roles' not in config:
            config['roles'] = {}
        
        for role_name in ['rekrut', 'member', 'moderator', 'admin', 'raid_leader']:
            role_id = request.form.get(f'role_{role_name}')
            if role_id:
                try:
                    config['roles'][role_name] = int(role_id)
                except ValueError:
                    flash(f'Ungültige ID für {role_name}!', 'error')
                    return render_template('roles.html', config=config)
        
        save_config(config)
        flash('Rollen-Konfiguration gespeichert!', 'success')
        return redirect(url_for('index'))
    
    return render_template('roles.html', config=config)

@app.route('/channels', methods=['GET', 'POST'])
@require_auth
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
@require_auth
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
    
    return render_template('permissions.html', 
                         config=config, 
                         all_commands=all_commands,
                         command_permissions=command_permissions)

@app.route('/update_permission', methods=['POST'])
@require_auth
def update_permission():
    """Update individual command permission"""
    config = load_config()
    
    command = request.form.get('command')
    selected_roles = request.form.getlist('roles')
    
    if not command or not selected_roles:
        return jsonify({'error': 'Command und Rollen sind erforderlich'}), 400
    
    if 'command_permissions' not in config:
        config['command_permissions'] = {}
    
    config['command_permissions'][command] = selected_roles
    save_config(config)
    
    return jsonify({'success': True, 'message': f'Berechtigungen für {command} aktualisiert'})

@app.route('/voice_promotion', methods=['GET', 'POST'])
@require_auth
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
@require_auth
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

@app.route('/reset_permissions', methods=['POST'])
@require_auth
def reset_permissions():
    """Reset all command permissions"""
    config = load_config()
    config['command_permissions'] = {}
    save_config(config)
    flash('Alle Berechtigungen wurden zurückgesetzt!', 'success')
    return redirect(url_for('permissions'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
