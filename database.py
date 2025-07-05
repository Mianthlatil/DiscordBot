import aiosqlite
import asyncio
from datetime import datetime, timedelta
import json

class Database:
    def __init__(self, db_path="guild_bot.db"):
        self.db_path = db_path
    
    async def initialize(self):
        """Initialize database tables"""
        async with aiosqlite.connect(self.db_path) as db:
            # Economy table
            await db.execute('''
                CREATE TABLE IF NOT EXISTS economy (
                    user_id INTEGER PRIMARY KEY,
                    balance INTEGER DEFAULT 0,
                    last_daily TIMESTAMP,
                    total_earned INTEGER DEFAULT 0
                )
            ''')
            
            # Voice activity tracking
            await db.execute('''
                CREATE TABLE IF NOT EXISTS voice_activity (
                    user_id INTEGER PRIMARY KEY,
                    total_minutes INTEGER DEFAULT 0,
                    session_start TIMESTAMP,
                    last_update TIMESTAMP
                )
            ''')
            
            # Raid registrations
            await db.execute('''
                CREATE TABLE IF NOT EXISTS raid_registrations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    raid_id TEXT,
                    user_id INTEGER,
                    username TEXT,
                    role TEXT,
                    notes TEXT,
                    registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(raid_id, user_id)
                )
            ''')
            
            # Temporary voice channels
            await db.execute('''
                CREATE TABLE IF NOT EXISTS temp_voice_channels (
                    channel_id INTEGER PRIMARY KEY,
                    owner_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Modmail threads
            await db.execute('''
                CREATE TABLE IF NOT EXISTS modmail_threads (
                    user_id INTEGER PRIMARY KEY,
                    channel_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'open'
                )
            ''')
            
            await db.commit()
    
    async def get_user_balance(self, user_id):
        """Get user's economy balance"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "SELECT balance FROM economy WHERE user_id = ?", (user_id,)
            )
            result = await cursor.fetchone()
            return result[0] if result else 0
    
    async def update_user_balance(self, user_id, amount):
        """Update user's balance"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                INSERT OR REPLACE INTO economy (user_id, balance, total_earned)
                VALUES (?, 
                    COALESCE((SELECT balance FROM economy WHERE user_id = ?), 0) + ?,
                    COALESCE((SELECT total_earned FROM economy WHERE user_id = ?), 0) + ?)
            ''', (user_id, user_id, amount, user_id, max(0, amount)))
            await db.commit()
    
    async def get_voice_activity(self, user_id):
        """Get user's voice activity"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "SELECT total_minutes, session_start FROM voice_activity WHERE user_id = ?", 
                (user_id,)
            )
            result = await cursor.fetchone()
            if result:
                return {"total_minutes": result[0], "session_start": result[1]}
            return {"total_minutes": 0, "session_start": None}
    
    async def update_voice_activity(self, user_id, minutes_to_add=0, session_start=None):
        """Update user's voice activity"""
        async with aiosqlite.connect(self.db_path) as db:
            if session_start:
                await db.execute('''
                    INSERT OR REPLACE INTO voice_activity (user_id, total_minutes, session_start, last_update)
                    VALUES (?, 
                        COALESCE((SELECT total_minutes FROM voice_activity WHERE user_id = ?), 0),
                        ?, CURRENT_TIMESTAMP)
                ''', (user_id, user_id, session_start))
            else:
                await db.execute('''
                    INSERT OR REPLACE INTO voice_activity (user_id, total_minutes, session_start, last_update)
                    VALUES (?, 
                        COALESCE((SELECT total_minutes FROM voice_activity WHERE user_id = ?), 0) + ?,
                        NULL, CURRENT_TIMESTAMP)
                ''', (user_id, user_id, minutes_to_add))
            await db.commit()
    
    async def register_for_raid(self, raid_id, user_id, username, role, notes=""):
        """Register user for a raid"""
        async with aiosqlite.connect(self.db_path) as db:
            try:
                await db.execute('''
                    INSERT INTO raid_registrations (raid_id, user_id, username, role, notes)
                    VALUES (?, ?, ?, ?, ?)
                ''', (raid_id, user_id, username, role, notes))
                await db.commit()
                return True
            except aiosqlite.IntegrityError:
                return False  # Already registered
    
    async def get_raid_registrations(self, raid_id):
        """Get all registrations for a raid"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute('''
                SELECT user_id, username, role, notes, registered_at 
                FROM raid_registrations 
                WHERE raid_id = ?
                ORDER BY registered_at
            ''', (raid_id,))
            return await cursor.fetchall()
    
    async def add_temp_voice_channel(self, channel_id, owner_id):
        """Add temporary voice channel to tracking"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                INSERT INTO temp_voice_channels (channel_id, owner_id)
                VALUES (?, ?)
            ''', (channel_id, owner_id))
            await db.commit()
    
    async def remove_temp_voice_channel(self, channel_id):
        """Remove temporary voice channel from tracking"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "DELETE FROM temp_voice_channels WHERE channel_id = ?", (channel_id,)
            )
            await db.commit()
    
    async def get_temp_voice_owner(self, channel_id):
        """Get owner of temporary voice channel"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "SELECT owner_id FROM temp_voice_channels WHERE channel_id = ?", (channel_id,)
            )
            result = await cursor.fetchone()
            return result[0] if result else None
