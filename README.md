# Telegram Appointment Monitor

A Python application that monitors the @Visasoon Telegram channel for visa appointment availability messages using your personal Telegram account. Features dynamic pattern management and push notifications.

## Features

- 🔍 **User Client Monitoring**: Uses Telethon to monitor @Visasoon channel with your personal account (no admin access needed)
- 🌍 **Dynamic Pattern Management**: Add/remove country/city patterns at runtime via bot commands
- 📨 **Push Notifications**: Optional bot integration for notifications with sound/vibration
- 🔗 **Direct Message Links**: Includes links to original appointment messages
- ⚙️ **Runtime Configuration**: Modify patterns without restarting the monitor
- 🔐 **Reliable Access**: Uses MTProto API for stable channel monitoring
- 💾 **Persistent Storage**: Patterns saved to JSON file for persistence across restarts

## Setup

### 1. Get Telegram API Credentials

1. Go to [https://my.telegram.org/apps](https://my.telegram.org/apps)
2. Log in with your phone number (same as your Telegram account)
3. Create a new application:
   - **App title:** "Appointment Monitor" (or any name)
   - **Short name:** "apt_monitor" (or any short name)
   - **Platform:** Choose "Desktop"
   - **Description:** "Monitor visa appointments"
4. Save your **API ID** (number) and **API Hash** (string)

### 2. Get Your Chat ID

1. Message [@userinfobot](https://t.me/userinfobot) on Telegram
2. It will reply with your chat ID (a number like `123456789`)

### 3. (Optional) Create a Bot for Push Notifications

1. Message [@BotFather](https://t.me/BotFather) on Telegram
2. Send `/newbot` and follow the instructions
3. Save the bot token for push notifications with sound/vibration
4. **Note**: This is optional - the monitor works without it, but notifications won't have sound

### 4. Install Dependencies

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\\Scripts\\activate

# Install dependencies
pip install -r requirements.txt
```

### 5. Configure Environment

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` with your actual values:
   ```
   API_ID=your_api_id_here
   API_HASH=your_api_hash_here
   YOUR_CHAT_ID=your_chat_id_here
   BOT_TOKEN=your_bot_token_here  # Optional, for push notifications
   ```

## Usage

### Start the Monitor

```bash
source venv/bin/activate  # Activate virtual environment
python main.py
```

On first run, you'll be prompted to enter your phone number and verification code to log in to Telegram.

### Bot Commands (Dynamic Configuration)

If you configured a bot token, you can manage patterns at runtime:

- `/start` - Show current configuration and available commands
- `/list` - Display all active monitoring patterns
- `/add Country · City` - Add a new pattern (e.g., `/add France · Edinburgh`)
- `/remove Country · City` - Remove an existing pattern
- `/status` - Show monitor status and configuration

### Initial Pattern Configuration

Default patterns are loaded from `config.py`. You can modify them there or use bot commands for dynamic updates:

```python
TARGET_PATTERNS = [
    "France · Edinburgh",
    "France · London", 
    "UK · Paris",
    "Germany · Berlin",
    # Add your desired patterns here
]
```

## How It Works

1. **User Client Connection**: Your personal Telegram account connects to monitor @Visasoon channel
2. **Message Detection**: Telethon client receives all new messages from the channel in real-time
3. **Pattern Matching**: Messages are checked against current patterns (loaded from JSON file)
4. **Smart Filtering**: Only appointment-related messages are processed (contains date/time patterns)
5. **Notification Delivery**: Matching messages trigger notifications via bot (with sound) or user account
6. **Dynamic Updates**: Add/remove patterns via bot commands without restarting

## Example Match

If monitoring for "France · Edinburgh" and this message appears in @Visasoon:

```
France · Edinburgh

Appointment Date: 
| 2025-09-30 [08:30, 09:00, 10:30, 11:00]
| 2025-10-01 [08:30, 09:00, 09:30, 10:00]
...
```

You'll receive:
```
🚨 APPOINTMENT ALERT 🚨

Matched Pattern: France · Edinburgh
Channel: @Visasoon
Time: 2025-09-15 10:30:00 UTC

Original Message:
─────────────────────
France · Edinburgh

Appointment Date: 
| 2025-09-30 [08:30, 09:00, 10:30, 11:00]
| 2025-10-01 [08:30, 09:00, 09:30, 10:00]
...

Direct Link: https://t.me/Visasoon/12345
```

## Configuration Options

### Adding New Patterns

To monitor additional country/city combinations, edit `config.py`:

```python
# Add to TARGET_PATTERNS list
TARGET_PATTERNS.append("Spain · Barcelona")
```

### Adjusting Pattern Matching

The bot uses regex patterns. Current pattern format: `Country · City`

- Case-insensitive matching
- Exact format matching (with the middle dot `·`)
- Automatically escapes special characters

## Pattern Management

### Adding Patterns at Runtime

```bash
# Send to your bot (if configured)
/add France · Edinburgh
/add Germany · Berlin
/add Spain · Barcelona
```

### Removing Patterns

```bash
/remove France · Edinburgh
/list  # Check remaining patterns
```

### Pattern Storage

- Patterns are stored in `patterns.json` 
- File is created automatically on first pattern modification
- Survives application restarts
- Falls back to `config.py` defaults if file is missing

## Troubleshooting

### Monitor Not Starting

1. **Check API Credentials**: Ensure `API_ID` and `API_HASH` in `.env` are correct
2. **Check Chat ID**: Verify `YOUR_CHAT_ID` is correct (get from @userinfobot)
3. **Phone Verification**: On first run, enter your phone number and verification code
4. **Session File**: Delete `session.session` file if login issues persist

### No Notifications Received

1. **Check Patterns**: Ensure patterns match exact format in channel messages
2. **Check Logs**: Monitor logs show when messages are received and matched
3. **Test Bot Commands**: Send `/status` to verify configuration
4. **Channel Access**: Confirm @Visasoon is accessible from your account

### Push Notifications Not Working

1. **Bot Token**: Ensure `BOT_TOKEN` is configured in `.env`
2. **Bot Chat**: Start a chat with your bot first
3. **Fallback**: Without bot token, notifications sent via user account (no sound)

### Common Errors

- `API_ID not found`: Check your `.env` file has correct API credentials
- `YOUR_CHAT_ID not found`: Check your `.env` file  
- `Unauthorized`: Invalid API credentials or session expired
- `Chat not found`: Invalid chat ID
- `Session expired`: Delete `session.session` and restart

## License

MIT License