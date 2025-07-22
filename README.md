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

A Discord bot that automatically processes Chinese text, generates pinyin pronunciation, translates to Japanese, and creates beautiful visual outputs with audio support. Now with **multi-channel support**, **cloud storage**, and **audio playback**!

## ✨ Features

- 🎯 **Multi-Channel Support**: Initialize the bot in any channel across multiple servers
- 📝 **Pinyin Generation**: Converts Chinese characters to pinyin with tone marks
- 🇯🇵 **Japanese Translation**: Uses Claude AI for accurate Chinese to Japanese translation
- 🖼️ **Visual Output**: Creates beautiful images with Chinese, pinyin, and Japanese text
- 🔊 **Audio Playback**: Generate and play Chinese pronunciation audio with gTTS
- ☁️ **Cloud Storage**: Firestore integration for persistent data across deployments
- 🔧 **Easy Management**: Simple commands to add/remove channels
- 🌐 **Cross-Server Support**: Works across multiple Discord servers simultaneously
- 🐳 **Docker Ready**: Complete Docker setup for easy deployment
- ⚡ **Fast Response**: Efficient processing with automatic cleanup
- 🎨 **Mixed Text Support**: Handles Chinese text mixed with English seamlessly

## 🆕 What's New (v3.0)

- **🔊 Audio Support**: Click button to hear Chinese pronunciation
- **☁️ Firestore Integration**: Cloud-based persistent storage (REQUIRED)
- **🤖 Claude AI Translation**: Superior Japanese translation quality
- **📷 Image Metadata**: Chinese text embedded in PNG for audio generation
- **🎨 Enhanced UI**: Beautiful Discord embeds for all responses
- **🔄 Improved Error Handling**: Better error messages and recovery
- **📱 Button Interface**: Interactive UI with audio playback buttons
- **🌍 Hugging Face Spaces**: Optimized for cloud deployment

## 🚀 Setup Instructions

### 1. Prerequisites

- Docker and Docker Compose installed
- Discord Bot Token
- Anthropic API Key (for Claude AI translation)
- Google Cloud Firestore Database (REQUIRED)

### 2. Get Discord Bot Token

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Create a new application
3. Go to "Bot" section
4. Create a bot and copy the token
5. Enable "Message Content Intent" in bot settings

### 3. Get Anthropic API Key

1. Go to [Anthropic Console](https://console.anthropic.com/)
2. Create an account and get your API key
3. This is used for high-quality Chinese to Japanese translation

### 4. Set up Firestore Database

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Create a new project
3. Enable Firestore Database
4. Create a service account key:
   - Go to Project Settings > Service Accounts
   - Generate new private key (JSON)
   - Download the JSON file

### 5. Installation

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
   cat > .env << EOF
   DISCORD_TOKEN=your_discord_token_here
   ANTHROPIC_API_KEY=your_anthropic_api_key_here
   GOOGLE_CLOUD_CREDENTIALS={"type":"service_account","project_id":"your-project-id",...}
   EOF
   ```

   **Important**: For `GOOGLE_CLOUD_CREDENTIALS`, paste the entire JSON content from your service account key file as a single line.

3. **Build and run with Docker**:
   ```bash
   # Build and start the bot
   docker-compose up -d
   
   # View logs
   docker-compose logs -f
   ```

### 6. Discord Server Setup

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
| `!backup` | Create backup of active channels in Firestore | Admin only |
| `!help` | Show comprehensive help information | Anyone |

### Usage
1. **Initialize a channel**: Run `!init` in any text channel
2. **Send Chinese text**: Type Chinese characters in the initialized channel
3. **Get instant results**: Bot replies with pinyin and Japanese translation image
4. **Play audio**: Click the 🔊 button to hear Chinese pronunciation
5. **Manage channels**: Use `!status` to see active channels, `!remove` to deactivate

## 💡 Example Usage

**Step 1**: Initialize channel
```
User: !init
Bot: ✅ Channel Initialized!
      This channel is now active for pinyin functionality.
      Server: My Server
      Channel: #general
      Storage: Firestore ☁️
```

**Step 2**: Send Chinese text
```
User: 你好世界
Bot: [Beautiful image containing:]
     - nǐ hǎo shì jiè (pinyin)
     - 你好世界 (Chinese - bold)
     - こんにちは世界 (Japanese - blue)
     [🔊 Play Audio] button
```

**Step 3**: Play audio
```
User: [Clicks 🔊 Play Audio button]
Bot: [Sends MP3 file with Chinese pronunciation]
```

**Step 4**: Check status
```
User: !status
Bot: 📊 Pinyin Bot Status
     Active Channels (3):
     • My Server - #general
     • Study Group - #chinese-practice
     • Language Exchange - #pinyin
     Storage: Firestore ☁️
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `DISCORD_TOKEN` | Discord bot token | ✅ Yes |
| `ANTHROPIC_API_KEY` | Anthropic API key for Claude AI | ✅ Yes |
| `GOOGLE_CLOUD_CREDENTIALS` | Full JSON service account key | ✅ Yes |

### File Structure
```
chinese-pinyin-bot/
├── app.py                 # Main bot code
├── requirements.txt       # Python dependencies
├── Dockerfile            # Docker configuration
├── docker-compose.yml    # Docker Compose setup
├── README.md             # This file
└── .env                  # Environment variables
```

## ☁️ Cloud Storage (Firestore)

The bot **requires** Firestore for persistent storage:

### Channel Data Storage
- **Collection**: `active_channels`
- **Document**: `channels_data`
- **Format**: Guild ID and Channel ID pairs
- **Auto-sync**: Real-time updates across deployments

### Backup System
- **Collection**: `channel_backups`
- **Documents**: Timestamped backups
- **Admin Command**: `!backup` creates manual backups
- **Auto-cleanup**: Removes invalid channels on startup

### Example Data Structure
```json
{
  "channels": [
    {"guild_id": 123456789, "channel_id": 987654321},
    {"guild_id": 111222333, "channel_id": 444555666}
  ],
  "last_updated": "2025-07-14T10:30:00Z",
  "total_channels": 2
}
```

## 🎵 Audio Features

### Text-to-Speech
- **Engine**: Google Text-to-Speech (gTTS)
- **Language**: Chinese (zh-cn)
- **Format**: MP3 audio files
- **Source**: Extracts Chinese text from PNG metadata

### Audio Generation Process
1. User clicks 🔊 button on bot's image response
2. Bot reads Chinese text from PNG metadata
3. Generates MP3 audio using gTTS
4. Sends audio file to Discord
5. Cleans up temporary files

## 🛠️ Troubleshooting

### Common Issues

1. **Bot not responding**:
   - Ensure the channel is initialized with `!init`
   - Check bot permissions in Discord
   - Verify all environment variables are set
   - Check Docker logs: `docker-compose logs -f`

2. **Firestore connection failed**:
   - Verify `GOOGLE_CLOUD_CREDENTIALS` is valid JSON
   - Check Firestore database is enabled
   - Ensure service account has Firestore permissions
   - Test with: `!status` command

3. **Translation failures**:
   - Verify `ANTHROPIC_API_KEY` is correct
   - Check Claude AI API quota/limits
   - Bot will show "Translation failed" in image

4. **Audio not working**:
   - Check if gTTS can access Google services
   - Verify bot has "Attach Files" permission
   - Try with simpler Chinese text

5. **Image generation failing**:
   - Check Docker logs for matplotlib errors
   - Ensure CJK fonts are installed
   - Verify sufficient memory allocation

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

### Environment Variable Setup

For **Hugging Face Spaces** or similar platforms:

1. **DISCORD_TOKEN**: Your bot token
2. **ANTHROPIC_API_KEY**: Your Claude API key
3. **GOOGLE_CLOUD_CREDENTIALS**: Full JSON content like:
   ```json
   {"type":"service_account","project_id":"your-project","private_key_id":"...","private_key":"-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n","client_email":"...","client_id":"...","auth_uri":"https://accounts.google.com/o/oauth2/auth","token_uri":"https://oauth2.googleapis.com/token","auth_provider_x509_cert_url":"https://www.googleapis.com/oauth2/v1/certs","client_x509_cert_url":"..."}
   ```

## 🏗️ Architecture

```
Discord Message → Channel Check → Pinyin Generation → Claude Translation → Image Creation → Audio Button → Discord Reply
```

### Components:
- **discord.py**: Discord API interaction and button handling
- **pypinyin**: Chinese to pinyin conversion with tone marks
- **anthropic**: Claude AI for superior Japanese translation
- **matplotlib**: Image generation with CJK font support
- **gTTS**: Text-to-speech audio generation
- **google-cloud-firestore**: Cloud-based persistent storage
- **Flask**: Health check endpoint for hosting platforms

### Data Flow:
1. User sends Chinese text in initialized channel
2. Bot detects Chinese characters using Unicode ranges
3. Generates pinyin with proper tone marks
4. Translates to Japanese using Claude AI
5. Creates formatted image with metadata
6. Sends image with audio button
7. User clicks button → generates and sends audio
8. All channel data synced to Firestore

## 🔒 Security Features

- **Non-root Docker execution**: Enhanced container security
- **Environment-based secrets**: No hardcoded credentials
- **Admin-only backup command**: Prevents unauthorized access
- **Input validation**: Proper error handling for all inputs
- **Minimal permissions**: Bot only needs basic Discord permissions
- **Automatic cleanup**: Removes access to invalid channels
- **Cloud storage**: Secure Firestore integration

## 📊 Performance

- **Response Time**: ~2-3 seconds per message
- **Memory Usage**: ~200-400MB baseline
- **CPU Usage**: Low, brief spikes during image/audio generation
- **Storage**: Cloud-based, unlimited scalability
- **Scalability**: Supports unlimited channels across servers
- **Audio Generation**: ~1-2 seconds per request

## 🆙 Migration Guide

### From v2.0 to v3.0

**Breaking Changes**:
1. **Firestore Required**: No longer optional, must be configured
2. **Anthropic API**: Replace Google Translate with Claude AI
3. **New Dependencies**: Update requirements.txt

**Migration Steps**:
1. **Set up Firestore**: Create database and service account
2. **Get Anthropic API key**: Sign up for Claude API
3. **Update environment variables**: Add new required variables
4. **Rebuild Docker image**: Use new requirements.txt
5. **Test functionality**: Verify all features work

### From v1.0 to v3.0

**Major Changes**:
1. **Channel Management**: `!init` any channel (no fixed names)
2. **Cloud Storage**: Firestore replaces local JSON files
3. **Audio Support**: New audio playback feature
4. **Better UI**: Discord embeds and button interactions

## 📄 License

This project is licensed under the MIT License - feel free to use and modify for personal or educational purposes.

## 🤝 Support

If you encounter issues:

1. **Check logs**: `docker-compose logs -f`
2. **Verify environment**: Ensure all API keys are correct
3. **Test commands**: Try `!help` and `!status`
4. **Firestore access**: Verify database permissions
5. **Reinitialize**: Use `!remove` then `!init` to reset channel

## 🎯 Roadmap

Future enhancements being considered:
- **Slash commands support**
- **Multiple language translation options**
- **Custom pinyin styles and tones**
- **Batch processing for multiple messages**
- **Web dashboard for channel management**
- **Voice message input support**
- **Advanced audio controls (speed, pitch)**
- **Favorites and history tracking**

---

**Happy learning Chinese! 🇨🇳✨**

*Now with enhanced AI translation and audio support!*