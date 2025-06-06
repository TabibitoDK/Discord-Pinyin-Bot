---
title: Chinese Pinyin Discord Bot
emoji: 📈
colorFrom: purple
colorTo: green
sdk: docker
pinned: false
license: mit
---

# Chinese Pinyin Discord Bot

A Discord bot that automatically processes Chinese text, generates pinyin pronunciation, translates to Japanese, and creates beautiful visual outputs. Now with **multi-channel support** and **persistent memory**!

## ✨ Features

- 🎯 **Multi-Channel Support**: Initialize the bot in any channel across multiple servers
- 📝 **Pinyin Generation**: Converts Chinese characters to pinyin with tone marks
- 🇯🇵 **Japanese Translation**: Uses Google Translate API for Chinese to Japanese translation
- 🖼️ **Visual Output**: Creates beautiful images with Chinese, pinyin, and Japanese text
- 💾 **Persistent Memory**: Remembers active channels even after bot restarts
- 🔧 **Easy Management**: Simple commands to add/remove channels
- 🌐 **Cross-Server Support**: Works across multiple Discord servers simultaneously
- 🐳 **Docker Ready**: Complete Docker setup for easy deployment
- ⚡ **Fast Response**: Efficient processing with automatic cleanup

## 🆕 What's New (v2.0)

- **Dynamic Channel Management**: No longer limited to a specific "pinyin" channel
- **`!init` Command**: Initialize any channel for pinyin functionality
- **`!remove` Command**: Remove channels from pinyin functionality
- **`!status` Command**: View all active channels across servers
- **`!backup` Command**: Create backups of channel configurations (Admin only)
- **JSON Persistence**: Channel data survives bot restarts
- **Automatic Cleanup**: Removes invalid channels on startup
- **Enhanced Help System**: Comprehensive command documentation
- **Beautiful Embeds**: All responses use Discord embeds for better UX

## 🚀 Setup Instructions

### 1. Prerequisites

- Docker and Docker Compose installed
- Discord Bot Token

### 2. Get Discord Bot Token

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Create a new application
3. Go to "Bot" section
4. Create a bot and copy the token
5. Enable "Message Content Intent" in bot settings

### 3. Installation

1. **Clone/Download the files**:
   ```bash
   # Create project directory
   mkdir chinese-pinyin-bot
   cd chinese-pinyin-bot
   
   # Copy all the provided files to this directory
   ```

2. **Set up environment variables**:
   ```bash
   # Create .env file
   echo "DISCORD_TOKEN=your_discord_token_here" > .env
   ```

3. **Build and run with Docker**:
   ```bash
   # Build and start the bot
   docker-compose up -d
   
   # View logs
   docker-compose logs -f
   ```

### 4. Discord Server Setup

1. **Invite the bot to your server**:
   - Go to Discord Developer Portal > Your App > OAuth2 > URL Generator
   - Select "bot" scope
   - Select permissions: "Send Messages", "Read Messages", "Attach Files", "Use Slash Commands"
   - Use the generated URL to invite the bot

2. **Initialize channels**:
   - Use `!init` in any channel you want to activate
   - No need to create specific channel names!

## 📋 Commands

### Setup Commands
| Command | Description | Permission |
|---------|-------------|------------|
| `!init` | Initialize current channel for pinyin functionality | Anyone |
| `!remove` | Remove current channel from pinyin functionality | Anyone |
| `!status` | Show all active channels across all servers | Anyone |
| `!backup` | Create backup of active channels | Admin only |
| `!help` | Show comprehensive help information | Anyone |

### Usage
1. **Initialize a channel**: Run `!init` in any text channel
2. **Send Chinese text**: Type Chinese characters in the initialized channel
3. **Get instant results**: Bot replies with pinyin and Japanese translation image
4. **Manage channels**: Use `!status` to see active channels, `!remove` to deactivate

## 💡 Example Usage

**Step 1**: Initialize channel
```
User: !init
Bot: ✅ Channel Initialized!
      This channel is now active for pinyin functionality.
```

**Step 2**: Send Chinese text
```
User: 你好世界
Bot: [Beautiful image containing:]
     - nǐ hǎo shì jiè (pinyin)
     - 你好世界 (Chinese)
     - こんにちは世界 (Japanese)
```

**Step 3**: Check status
```
User: !status
Bot: 📊 Pinyin Bot Status
     Active Channels (3):
     • My Server - #general
     • Study Group - #chinese-practice
     • Language Exchange - #pinyin
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `DISCORD_TOKEN` | Discord bot token | ✅ Yes |

### File Structure
```
chinese-pinyin-bot/
├── app.py                 # Main bot code
├── requirements.txt       # Python dependencies
├── Dockerfile            # Docker configuration
├── docker-compose.yml    # Docker Compose setup
├── active_channels.json  # Persistent channel data (auto-created)
└── channels_backup_*.json # Manual backups (created by !backup)
```

## 🗂️ Data Persistence

The bot automatically saves active channels to `active_channels.json`:

```json
{
  "channels": [
    [123456789012345678, 987654321098765432],
    [null, 111222333444555666]
  ],
  "last_updated": "2025-06-06T10:30:00.000000"
}
```

- **Guild ID**: Server identifier (null for DMs)
- **Channel ID**: Channel identifier
- **Auto-save**: Updates when channels are added/removed
- **Auto-cleanup**: Removes invalid channels on startup

## 🛠️ Troubleshooting

### Common Issues

1. **Bot not responding**:
   - Ensure the channel is initialized with `!init`
   - Check bot permissions in Discord
   - Verify `DISCORD_TOKEN` is correct
   - Check Docker logs: `docker-compose logs`

2. **Commands not working**:
   - Verify bot has "Send Messages" permission
   - Check if channel is properly initialized
   - Try reinitializing with `!init`

3. **Translation failures**:
   - Bot will show "Translation failed" in image
   - Check internet connectivity
   - Google Translate API has rate limits

4. **Image generation failing**:
   - Check Docker logs for matplotlib errors
   - Ensure sufficient memory allocation
   - Font issues - fonts are included in Docker image

### Docker Commands

```bash
# View real-time logs
docker-compose logs -f

# Restart bot
docker-compose restart

# Stop bot
docker-compose down

# Rebuild after code changes
docker-compose up -d --build

# Check container status
docker-compose ps

# Access container shell
docker-compose exec app bash
```

### Backup & Recovery

```bash
# Manual backup (use !backup command in Discord)
!backup

# View backup files
ls channels_backup_*.json

# Restore from backup (copy to active_channels.json)
cp channels_backup_20250606_103000.json active_channels.json
docker-compose restart
```

## 🏗️ Architecture

```
Discord Message → Channel Check → Pinyin Generation → Translation → Image Creation → Discord Reply
```

### Components:
- **discord.py**: Discord API interaction and command handling
- **pypinyin**: Chinese to pinyin conversion with tone marks
- **googletrans**: Chinese to Japanese translation
- **matplotlib**: Image generation with CJK font support
- **Flask**: Health check endpoint for hosting platforms
- **JSON**: Persistent data storage

### Flow:
1. User sends message in initialized channel
2. Bot detects Chinese characters
3. Generates pinyin with tone marks
4. Translates to Japanese
5. Creates formatted image
6. Replies with image attachment

## 🔒 Security Features

- **Non-root Docker execution**: Enhanced container security
- **Environment-based configuration**: No hardcoded secrets
- **Admin-only backup command**: Prevents unauthorized access
- **Input validation**: Proper error handling for all inputs
- **Minimal permissions**: Bot only needs basic message permissions
- **Automatic cleanup**: Removes access to invalid channels

## 📊 Performance

- **Response Time**: ~2-3 seconds per message
- **Memory Usage**: ~150-300MB baseline
- **CPU Usage**: Low, brief spikes during image generation
- **Storage**: Minimal, only JSON files for persistence
- **Scalability**: Supports unlimited channels across servers

## 🆙 Migration from v1.0

If you're upgrading from the old version:

1. **Automatic migration**: Existing "pinyin" channels need to be re-initialized
2. **Use `!init`**: Run in your existing pinyin channels
3. **New flexibility**: You can now use any channel name
4. **Backup old data**: Use `!backup` to save configurations

## 📄 License

This project is licensed under the MIT License - feel free to use and modify for personal or educational purposes.

## 🤝 Support

If you encounter issues:

1. **Check logs**: `docker-compose logs -f`
2. **Verify setup**: Ensure bot token is correct
3. **Test commands**: Try `!help` and `!status`
4. **Reinitialize**: Use `!remove` then `!init` to reset channel
5. **Check permissions**: Ensure bot can send messages and attach files

## 🎯 Roadmap

Future enhancements being considered:
- **Slash commands support**
- **Multiple language translation options**
- **Custom pinyin styles**
- **Batch processing**
- **Web dashboard**
- **Database integration**

---

**Happy learning Chinese! 🇨🇳✨**