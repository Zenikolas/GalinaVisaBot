"""Telegram user client to monitor @Visasoon channel for appointment availability."""

import asyncio
import logging
import os
import re
from typing import Optional

from dotenv import load_dotenv
from telethon import TelegramClient, events
from telethon.tl.types import User
import aiohttp
import json
from pathlib import Path

from config import Config

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class PatternManager:
    """Manages dynamic pattern configuration."""
    
    def __init__(self, config_file: str = "patterns.json"):
        self.config_file = Path(config_file)
        self.patterns = self.load_patterns()
    
    def load_patterns(self) -> list:
        """Load patterns from file or use defaults."""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading patterns: {e}")
        
        # Return default patterns if file doesn't exist or error
        return Config.TARGET_PATTERNS.copy()
    
    def save_patterns(self):
        """Save patterns to file."""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.patterns, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving patterns: {e}")
    
    def add_pattern(self, pattern: str) -> bool:
        """Add a new pattern."""
        if pattern not in self.patterns:
            self.patterns.append(pattern)
            self.save_patterns()
            return True
        return False
    
    def remove_pattern(self, pattern: str) -> bool:
        """Remove a pattern."""
        if pattern in self.patterns:
            self.patterns.remove(pattern)
            self.save_patterns()
            return True
        return False
    
    def get_patterns(self) -> list:
        """Get current patterns."""
        return self.patterns.copy()
    
    def get_compiled_patterns(self) -> list:
        """Get compiled regex patterns for flexible country/city matching."""
        patterns = []
        for pattern in self.patterns:
            # Parse pattern as "country,city" or handle existing "country · city" format
            if ',' in pattern:
                country, city = [p.strip() for p in pattern.split(',', 1)]
            elif ' · ' in pattern or '\u00b7' in pattern:
                # Handle existing patterns with middle dot
                normalized = pattern.replace('\u00b7', ' · ')
                country, city = [p.strip() for p in normalized.split(' · ', 1)]
            else:
                # Skip malformed patterns
                continue
            
            # Create flexible regex that finds country and city anywhere in the message
            # Matches: "🇨🇾 Cyprus · London", "France - London", "Cyprus, London", etc.
            flexible_pattern = rf'(?=.*\b{re.escape(country)}\b)(?=.*\b{re.escape(city)}\b)'
            compiled_pattern = re.compile(flexible_pattern, re.IGNORECASE | re.DOTALL)
            patterns.append(compiled_pattern)
        return patterns

class AppointmentMonitor:
    """Telethon client to monitor Visasoon channel for appointment availability."""
    
    def __init__(self, api_id: int, api_hash: str, your_chat_id: int, bot_token: str = None):
        self.api_id = api_id
        self.api_hash = api_hash
        self.your_chat_id = your_chat_id
        self.bot_token = bot_token
        self.pattern_manager = PatternManager()
        self.appointment_pattern = Config.get_appointment_message_pattern()
        
        # Create Telethon client for monitoring
        self.client = TelegramClient('session', api_id, api_hash)
        
        # Create bot client for commands (if bot token provided)
        self.bot_client = None
        if bot_token:
            self.bot_client = TelegramClient('bot_session', api_id, api_hash)
    
    def check_message_for_patterns(self, message_text: str) -> Optional[str]:
        """Check if message contains appointment info and matches target patterns."""
        # First check if this looks like an appointment message
        if not self.appointment_pattern.search(message_text):
            return None
        
        # Get current patterns and compiled patterns
        current_patterns = self.pattern_manager.get_patterns()
        compiled_patterns = self.pattern_manager.get_compiled_patterns()
        
        # Check for country/city patterns
        for i, pattern in enumerate(compiled_patterns):
            if pattern.search(message_text):
                return current_patterns[i]
        
        return None
    
    async def send_notification(self, matched_pattern: str, message_text: str, message_link: str = None):
        """Send notification to user via bot (for push notifications)."""
        notification = (
            f"🚨 **APPOINTMENT ALERT** 🚨\n\n"
            f"**Matched Pattern:** {matched_pattern}\n"
            f"**Channel:** {Config.TARGET_CHANNEL}\n\n"
            f"**Original Message:**\n"
            f"─────────────────────\n"
            f"{message_text}"
        )
        
        if message_link:
            notification += f"\n\n**Direct Link:** {message_link}"
        
        try:
            if self.bot_token:
                # Send via bot for push notifications
                await self.send_bot_message(notification)
            else:
                # Fallback to user account (no push notifications)
                await self.client.send_message(self.your_chat_id, notification)
            logger.info("Notification sent successfully")
        except Exception as e:
            logger.error(f"Failed to send notification: {e}")
    
    async def send_bot_message(self, text: str):
        """Send message via Telegram Bot API for push notifications."""
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        data = {
            'chat_id': self.your_chat_id,
            'text': text,
            'parse_mode': 'Markdown',
            'disable_web_page_preview': False
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=data) as response:
                if response.status != 200:
                    raise Exception(f"Bot API error: {response.status}")
    
    async def setup_bot_commands(self):
        """Set up bot command handlers."""
        if not self.bot_client:
            return
        
        await self.bot_client.start(bot_token=self.bot_token)
        
        @self.bot_client.on(events.NewMessage(pattern='/start'))
        async def start_command(event):
            if event.sender_id != self.your_chat_id:
                return
            
            patterns = self.pattern_manager.get_patterns()
            message = (
                f"🤖 **Appointment Monitor Bot**\n\n"
                f"**Monitoring:** {Config.TARGET_CHANNEL}\n"
                f"**Active Patterns:** {len(patterns)}\n\n"
                f"**Commands:**\n"
                f"• `/list` - Show current patterns\n"
                f"• `/add Country City` - Add new pattern (e.g., `/add France London`)\n"
                f"• `/remove Country City` - Remove pattern\n"
                f"• `/status` - Show monitor status\n\n"
                f"**Current Patterns:**\n"
            )
            for pattern in patterns:
                message += f"• {pattern}\n"
            
            await event.reply(message)
        
        @self.bot_client.on(events.NewMessage(pattern='/list'))
        async def list_patterns(event):
            if event.sender_id != self.your_chat_id:
                return
            
            patterns = self.pattern_manager.get_patterns()
            if patterns:
                message = "📋 **Current Patterns:**\n\n"
                for i, pattern in enumerate(patterns, 1):
                    message += f"{i}. {pattern}\n"
            else:
                message = "❌ No patterns configured"
            
            await event.reply(message)
        
        @self.bot_client.on(events.NewMessage(pattern=r'/add (.+) (.+)'))
        async def add_pattern(event):
            if event.sender_id != self.your_chat_id:
                return
            
            country = event.pattern_match.group(1).strip()
            city = event.pattern_match.group(2).strip()
            pattern = f"{country},{city}"
            
            if self.pattern_manager.add_pattern(pattern):
                await event.reply(f"✅ Added pattern: `{country}` in `{city}`")
                logger.info(f"Pattern added: {pattern}")
            else:
                await event.reply(f"❌ Pattern already exists: `{country}` in `{city}`")
        
        @self.bot_client.on(events.NewMessage(pattern=r'/remove (.+) (.+)'))
        async def remove_pattern(event):
            if event.sender_id != self.your_chat_id:
                return
            
            country = event.pattern_match.group(1).strip()
            city = event.pattern_match.group(2).strip()
            pattern = f"{country},{city}"
            
            if self.pattern_manager.remove_pattern(pattern):
                await event.reply(f"✅ Removed pattern: `{country}` in `{city}`")
                logger.info(f"Pattern removed: {pattern}")
            else:
                await event.reply(f"❌ Pattern not found: `{country}` in `{city}`")
        
        @self.bot_client.on(events.NewMessage(pattern='/status'))
        async def status_command(event):
            if event.sender_id != self.your_chat_id:
                return
            
            patterns = self.pattern_manager.get_patterns()
            message = (
                f"📊 **Monitor Status**\n\n"
                f"**Channel:** {Config.TARGET_CHANNEL}\n"
                f"**Active Patterns:** {len(patterns)}\n"
                f"**Your Chat ID:** {self.your_chat_id}\n"
                f"**Bot Token:** {'✅ Configured' if self.bot_token else '❌ Not configured'}\n"
            )
            await event.reply(message)
    
    async def start_monitoring(self):
        """Start monitoring the channel."""
        logger.info("Starting Appointment Monitor...")
        logger.info(f"Monitoring channel: {Config.TARGET_CHANNEL}")
        
        current_patterns = self.pattern_manager.get_patterns()
        logger.info(f"Target patterns: {current_patterns}")
        logger.info(f"Your chat ID: {self.your_chat_id}")
        
        # Start the monitoring client
        await self.client.start()
        
        # Get user info
        me = await self.client.get_me()
        logger.info(f"Logged in as: {me.first_name} (@{me.username})")
        
        # Start bot client for commands
        if self.bot_client:
            await self.setup_bot_commands()
            logger.info("Bot commands enabled")
        
        # Set up event handler for new messages in the target channel
        @self.client.on(events.NewMessage(chats=Config.TARGET_CHANNEL))
        async def handle_new_message(event):
            logger.info(f"New message received from {Config.TARGET_CHANNEL}")
            
            message_text = event.message.text or ""
            logger.info(f"Message text: {message_text[:100]}...")
            
            # Check if message matches our patterns
            matched_pattern = self.check_message_for_patterns(message_text)
            
            if matched_pattern:
                logger.info(f"Found matching appointment message for pattern: {matched_pattern}")
                
                # Create message link
                message_link = f"https://t.me/{Config.TARGET_CHANNEL.lstrip('@')}/{event.message.id}"
                
                # Send notification
                await self.send_notification(matched_pattern, message_text, message_link)
            else:
                logger.info("Message doesn't match any patterns")
        
        logger.info("Monitor started. Press Ctrl+C to stop.")
        logger.info("Send /start to the bot to manage patterns")
        
        # Keep the client running
        await self.client.run_until_disconnected()
    

async def main():
    """Main function to run the monitor."""
    # Get environment variables
    api_id = os.getenv('API_ID')
    api_hash = os.getenv('API_HASH')
    bot_token = os.getenv('BOT_TOKEN')  # Optional, for push notifications
    your_chat_id = os.getenv('YOUR_CHAT_ID')
    
    if not api_id:
        logger.error("API_ID environment variable is required")
        logger.error("Get it from https://my.telegram.org/apps")
        return
    
    if not api_hash:
        logger.error("API_HASH environment variable is required")
        logger.error("Get it from https://my.telegram.org/apps")
        return
    
    if not your_chat_id:
        logger.error("YOUR_CHAT_ID environment variable is required")
        return
    
    try:
        # Create and start monitor
        monitor = AppointmentMonitor(
            api_id=int(api_id),
            api_hash=api_hash,
            your_chat_id=int(your_chat_id),
            bot_token=bot_token
        )
        
        await monitor.start_monitoring()
        
    except KeyboardInterrupt:
        logger.info("Monitor stopped by user")
    except Exception as e:
        logger.error(f"Monitor crashed with error: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())