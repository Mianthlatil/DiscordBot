import json
import discord
from flask import Flask, request, render_template, redirect, url_for

app = Flask(__name__)
bot_instance = None  # Setze dies auf deine Bot-Instanz in web_config

@app.route("/permissions")
def permissions_page():
    guild_id = request.args.get("guild_id")
    if not guild_id:
        return "Guild-ID fehlt", 400

    from web_config import bot_instance
    if not bot_instance:
        return "Bot nicht gestartet", 500

    guild = discord.utils.get(bot_instance.guilds, id=int(guild_id))
    if not guild:
        return "Bot ist nicht auf diesem Server", 403

    roles = [r for r in guild.roles if r.name != "@everyone"]
    commands = ["ban", "mute", "raid", "setup", "verify"]

    return render_template("permissions_page.html", guild=guild, roles=roles, commands=commands)

@app.route("/save_permissions", methods=["POST"])
def save_permissions():
    guild_id = request.form.get("guild_id")
    if not guild_id:
        return "Guild-ID fehlt", 400

    try:
        with open("config.json", "r", encoding="utf-8") as f:
            config = json.load(f)
    except FileNotFoundError:
        config = {}

    if "servers" not in config:
        config["servers"] = {}
    if guild_id not in config["servers"]:
        config["servers"][guild_id] = {}

    permissions = {}
    commands = ["ban", "mute", "raid", "setup", "verify"]
    for cmd in commands:
        mode = request.form.get(f"mode_{cmd}") or "whitelist"
        selected_roles = request.form.getlist(f"roles_{cmd}")
        permissions[cmd] = {
            "mode": mode,
            "roles": [int(rid) for rid in selected_roles]
        }

    config["servers"][guild_id]["permissions"] = permissions

    with open("config.json", "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4, ensure_ascii=False)

    return "✅ Berechtigungen gespeichert."

def check_permission(member, guild_id, command_name):
    try:
        with open("config.json", "r", encoding="utf-8") as f:
            config = json.load(f)

        permissions = config["servers"].get(str(guild_id), {}).get("permissions", {})
        command_rule = permissions.get(command_name)
        if not command_rule:
            return True

        mode = command_rule.get("mode", "whitelist")
        allowed_roles = command_rule.get("roles", [])

        user_role_ids = [role.id for role in member.roles]
        match = any(role_id in user_role_ids for role_id in allowed_roles)

        if mode == "whitelist":
            return match
        elif mode == "blacklist":
            return not match
        else:
            return True

    except Exception as e:
        print(f"Berechtigungsfehler: {e}")
        return False