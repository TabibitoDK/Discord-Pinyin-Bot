---
title: chinnese-pinyin-bot
emoji: 🦙
colorFrom: indigo
colorTo: pink
sdk: docker
pinned: false
---
# Chinese Pinyin Discord Bot

A Discord bot that automatically processes Chinese text, generates pinyin pronunciation, translates to Japanese, and creates beautiful visual outputs.

## Features

- 🎯 **Automatic Processing**: Monitors a specific Discord channel for Chinese text
- 📝 **Pinyin Generation**: Converts Chinese characters to pinyin with tone marks
- 🇯🇵 **Japanese Translation**: Uses Google Translate API for Chinese to Japanese translation
- 🖼️ **Visual Output**: Creates beautiful HTML pages and renders them as images
- 🐳 **Docker Ready**: Complete Docker setup for easy deployment
- ⚡ **Fast Response**: Efficient processing with typing indicators

## Setup Instructions

### 1. Prerequisites

- Docker and Docker Compose installed
- Discord Bot Token
- Google Cloud Translation API Key

### 2. Get Required API Keys

#### Discord Bot Token:
1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Create a new application
3. Go to "Bot" section
4. Create a bot and copy the token
5. Enable "Message Content Intent" in bot settings

#### Google Translate API Key:
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Enable the "Cloud Translation API"
3. Create credentials (API Key)
4. Copy the API key

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
   # Copy the example file
   cp .env.example .env
   
   # Edit .env file with your actual keys
   nano .env
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
   - Select permissions: "Send Messages", "Read Messages", "Attach Files"
   - Use the generated URL to invite the bot

2. **Create a pinyin channel** (or use existing channel):
   - Create a text channel named "pinyin" (or change `PINYIN_CHANNEL` in .env)

## Usage

### Automatic Processing

1. **Send Chinese text** in the designated channel (default: `#pinyin`)
2. **Bot automatically detects** Chinese characters
3. **Generates response** with:
   - Original Chinese text
   - Pinyin pronunciation with tones
   - Japanese translation
   - Beautiful formatted image

### Manual Commands

- `!test 你好世界` - Test the bot with Chinese text
- `!help_pinyin` - Show help information

## Example

**Input**: `你好世界` (in #pinyin channel)

**Output**: Beautiful image containing:
- **Original**: 你好世界
- **Pinyin**: nǐ hǎo shì jiè
- **Japanese**: こんにちは世界

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DISCORD_TOKEN` | Discord bot token | Required |
| `GOOGLE_API_KEY` | Google Translate API key | Required |
| `PINYIN_CHANNEL` | Channel name to monitor | `pinyin` |

### Docker Configuration

The bot runs in a secure Docker container with:
- Headless Chrome for rendering
- Non-root user for security
- Memory and CPU limits
- Automatic restart policy
- Proper logging configuration

## Troubleshooting

### Common Issues

1. **Bot not responding**:
   - Check if bot has proper permissions in Discord
   - Verify environment variables are set correctly
   - Check Docker logs: `docker-compose logs`

2. **Translation not working**:
   - Verify Google API key is correct
   - Ensure Translation API is enabled in Google Cloud
   - Check API quota limits

3. **Image generation failing**:
   - Chrome/ChromeDriver issues - check Docker logs
   - Memory issues - increase Docker memory limit

### Docker Commands

```bash
# View logs
docker-compose logs -f

# Restart bot
docker-compose restart

# Stop bot
docker-compose down

# Rebuild after changes
docker-compose up -d --build

# Check container status
docker-compose ps
```

## Architecture

```
Discord Message → Bot Detection → Pinyin Generation → Translation → HTML Creation → Screenshot → Discord Reply
```

The bot uses:
- **discord.py**: Discord API interaction
- **pypinyin**: Chinese to pinyin conversion
- **Google Translate API**: Chinese to Japanese translation
- **Selenium + Chrome**: HTML rendering to image
- **PIL**: Image processing and optimization

## Security Features

- Non-root container execution
- Minimal Docker image with only required dependencies
- Environment variable based configuration
- No hardcoded secrets
- Proper error handling and logging

## Performance

- **Response Time**: ~3-5 seconds per message
- **Memory Usage**: ~200-400MB
- **CPU Usage**: Low, spikes during image generation
- **Network**: Minimal, only API calls

## License

This project is provided as-is for educational and personal use.

## Support

If you encounter issues:
1. Check the troubleshooting section
2. Review Docker logs
3. Verify API keys and permissions
4. Ensure proper Discord bot setup