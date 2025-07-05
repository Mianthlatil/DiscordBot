# Discord Guild Bot

## Overview

This is a comprehensive Discord guild management bot designed for gaming communities, specifically featuring Dune Awakening raid coordination. The bot provides economy systems, voice channel management, modmail functionality, raid planning, role progression, and temporary voice channels.

## System Architecture

### Backend Architecture
- **Language**: Python 3.7+
- **Framework**: discord.py with commands extension
- **Database**: SQLite with aiosqlite for async operations
- **Configuration**: JSON-based configuration file
- **Architecture Pattern**: Cog-based modular system

### Core Components
- **Main Bot**: Entry point with event handlers and cog loading
- **Database Layer**: Centralized SQLite database management
- **Cog System**: Modular feature separation for maintainability
- **Utilities**: Helper functions and permission decorators

## Key Components

### 1. Economy System (`cogs/economy.py`)
- Virtual currency ("Spice") management
- Daily bonus claims with cooldown tracking
- Voice activity rewards (25 Spice per hour)
- Raid completion bonuses (500 Spice)
- Balance checking and transaction logging

### 2. Voice Management (`cogs/voice_management.py`)
- Voice channel locking/unlocking
- Activity tracking for rewards
- Administrative controls for moderators
- Automatic voice time accumulation

### 3. Raid System (`cogs/raid_system.py`)
- Raid announcement creation
- Role-based registration (DPS, Tank, Healer, etc.)
- Emoji-based signup system
- Registration management and tracking

### 4. Modmail System (`cogs/modmail.py`)
- Private message ticket creation
- Staff response threading
- Ticket status management
- Automated channel creation in designated category

### 5. Temporary Voice Channels (`cogs/temp_voice.py`)
- On-demand voice channel creation
- User-controlled channel permissions
- Automatic cleanup when empty
- Customizable channel names and limits

### 6. Role Promotion (`cogs/role_promotion.py`)
- Automatic promotion from "Rekrut" to "Member"
- Voice activity requirement tracking (24 hours default)
- Periodic eligibility checking (5-minute intervals)
- Configurable promotion thresholds

## Data Flow

### Database Schema
```sql
-- Economy tracking
economy: user_id, balance, last_daily, total_earned

-- Voice activity monitoring
voice_activity: user_id, total_minutes, session_start, last_update

-- Raid participation
raid_registrations: raid_id, user_id, username, role, notes, registered_at

-- Temporary channels
temp_voice_channels: channel_id, owner_id, created_at
```

### Permission System
- Role-based command access control
- Configurable role hierarchy in config.json
- Decorator-based permission checking
- Server owner bypass for all restrictions

## External Dependencies

### Required Libraries
- `discord.py`: Discord API interaction
- `aiosqlite`: Async SQLite database operations
- `asyncio`: Asynchronous programming support
- Standard library: `json`, `datetime`, `os`

### Discord Permissions Required
- `message_content`: Read message content
- `voice_states`: Monitor voice channel activity
- `members`: Access member information
- `guilds`: Server management capabilities
- `manage_channels`: Create/modify voice channels
- `manage_roles`: Role promotion functionality

## Deployment Strategy

### Environment Setup
1. Install Python 3.7+
2. Install required dependencies via pip
3. Configure Discord bot token
4. Set up config.json with guild-specific settings
5. Initialize SQLite database on first run

### Configuration Requirements
- Guild-specific role IDs for permission system
- Channel IDs for modmail categories and announcements
- Economic parameters (daily bonuses, rewards)
- Voice promotion thresholds

### Scaling Considerations
- Single-guild design (can be modified for multi-guild)
- SQLite suitable for small to medium communities
- Memory-efficient cog loading system
- Configurable check intervals for performance tuning

## Changelog
- July 05, 2025. Initial Discord bot setup completed
- July 05, 2025. Bot successfully deployed and connected to Discord
- July 05, 2025. All 6 core modules loaded and functional
- July 05, 2025. Added comprehensive Event System with Attack/Def/Crawler/Carrier roles
- July 05, 2025. Implemented Slash Commands for all major features
- July 05, 2025. Created integrated Command Overview system
- July 05, 2025. Removed daily command from economy system per user request
- July 05, 2025. Enhanced Event System with custom titles and /event-edit command
- July 05, 2025. Restricted Crawler/Carrier roles to command-only assignment
- July 05, 2025. Fixed database schema for event titles and improved UI
- July 05, 2025. Enhanced ModMail system to work in any channel with privacy features
- July 05, 2025. Added player name display in event registrations by role

## User Preferences

Preferred communication style: Simple, everyday language.