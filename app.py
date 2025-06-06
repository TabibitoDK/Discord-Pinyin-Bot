import discord
from discord.ext import commands
import matplotlib.pyplot as plt
from pypinyin import pinyin, Style
from googletrans import Translator
import io
import os
import asyncio
import threading
import json
from flask import Flask
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.font_manager as fm

# Set matplotlib cache directory to a writable location
os.environ['MPLCONFIGDIR'] = '/tmp/matplotlib'
# Create the directory if it doesn't exist
os.makedirs('/tmp/matplotlib', exist_ok=True)

# Clear matplotlib font cache and rebuild
fm._load_fontmanager(try_read_cache=False)

# Set font properties for CJK support
plt.rcParams['font.family'] = ['Noto Sans CJK SC', 'Noto Sans CJK JP', 'DejaVu Sans', 'sans-serif']
plt.rcParams['axes.unicode_minus'] = False

# Flask app for health check (required for Hugging Face Spaces)
app = Flask(__name__)

@app.route('/')
def health_check():
    return "Discord bot is running!"

# Store active channels (guild_id, channel_id) pairs
active_channels = set()
CHANNELS_FILE = 'active_channels.json'

def load_active_channels():
    """Load active channels from JSON file."""
    global active_channels
    try:
        if os.path.exists(CHANNELS_FILE):
            with open(CHANNELS_FILE, 'r') as f:
                data = json.load(f)
                # Convert list of lists back to set of tuples
                active_channels = set(tuple(channel) for channel in data.get('channels', []))
                print(f"Loaded {len(active_channels)} active channels from {CHANNELS_FILE}")
        else:
            active_channels = set()
            print(f"No existing {CHANNELS_FILE} found, starting with empty channel list")
    except Exception as e:
        print(f"Error loading active channels: {e}")
        active_channels = set()

def save_active_channels():
    """Save active channels to JSON file."""
    try:
        # Convert set of tuples to list of lists for JSON serialization
        data = {
            'channels': [list(channel) for channel in active_channels],
            'last_updated': discord.utils.utcnow().isoformat()
        }
        with open(CHANNELS_FILE, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"Saved {len(active_channels)} active channels to {CHANNELS_FILE}")
    except Exception as e:
        print(f"Error saving active channels: {e}")

def get_pinyin_with_tone_marks(text):
    return [py[0].replace("u:", "ü") for py in pinyin(text, style=Style.TONE)]

def translate_chinese_to_japanese(text):
    translator = Translator()
    try:
        result = translator.translate(text, src='zh-cn', dest='ja')
        return result.text
    except Exception as e:
        print(f"Translation error: {e}")
        return "Translation failed"

def create_image(text):
    if not text.strip():
        return None
    
    try:
        pinyin_list = get_pinyin_with_tone_marks(text)
        japanese_translation = translate_chinese_to_japanese(text)
        
        # Create figure with appropriate size
        fig_width = max(len(text) * 0.8, 4)
        fig, ax = plt.subplots(figsize=(fig_width, 3))
        
        # Find a suitable font
        font_prop = fm.FontProperties(family=['Noto Sans CJK SC', 'Noto Sans CJK JP', 'DejaVu Sans'])
        
        # Add Chinese characters and pinyin
        for i, (char, py) in enumerate(zip(text, pinyin_list)):
            x = i + 0.5
            # Pinyin on top
            ax.text(x, 0.7, py, fontsize=14, ha='center', va='bottom', 
                   fontproperties=font_prop, weight='normal')
            # Chinese character in middle
            ax.text(x, 0.5, char, fontsize=20, ha='center', va='center', 
                   fontproperties=font_prop, weight='bold')
        
        # Japanese translation at bottom
        ax.text(len(text)/2, 0.2, japanese_translation, fontsize=12, 
               ha='center', va='top', color='blue', fontproperties=font_prop)
        
        ax.set_xlim(0, len(text))
        ax.set_ylim(0, 1)
        ax.axis('off')
        
        # Save to bytes buffer
        buf = io.BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight', dpi=300, 
                   facecolor='white', edgecolor='none')
        plt.close()
        buf.seek(0)
        
        return buf
    except Exception as e:
        print(f"Error creating image: {e}")
        return None

# Discord bot setup
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)  # Disable default help

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    print(f'Bot is in {len(bot.guilds)} guilds')
    
    # Load active channels from file
    load_active_channels()
    
    # Clean up invalid channels (channels that no longer exist)
    await cleanup_invalid_channels()

async def cleanup_invalid_channels():
    """Remove channels that no longer exist or bot no longer has access to."""
    invalid_channels = set()
    
    for guild_id, channel_id in active_channels.copy():
        try:
            if guild_id is None:  # DM channel
                channel = bot.get_channel(channel_id)
                if channel is None:
                    invalid_channels.add((guild_id, channel_id))
            else:  # Guild channel
                guild = bot.get_guild(guild_id)
                if guild is None:
                    invalid_channels.add((guild_id, channel_id))
                    continue
                
                channel = guild.get_channel(channel_id)
                if channel is None:
                    invalid_channels.add((guild_id, channel_id))
        except Exception as e:
            print(f"Error checking channel {guild_id}/{channel_id}: {e}")
            invalid_channels.add((guild_id, channel_id))
    
    if invalid_channels:
        for channel_key in invalid_channels:
            active_channels.discard(channel_key)
        
        print(f"Cleaned up {len(invalid_channels)} invalid channels")
        save_active_channels()

@bot.command(name='init')
async def init_channel(ctx):
    """Initialize the current channel for pinyin functionality."""
    channel_id = ctx.channel.id
    guild_id = ctx.guild.id if ctx.guild else None
    
    # Create channel identifier
    channel_key = (guild_id, channel_id)
    
    if channel_key in active_channels:
        await ctx.send(f"📌 This channel is already initialized for pinyin functionality!")
        return
    
    # Add channel to active channels
    active_channels.add(channel_key)
    
    # Save to file
    save_active_channels()
    
    guild_name = ctx.guild.name if ctx.guild else "DM"
    channel_name = ctx.channel.name if hasattr(ctx.channel, 'name') else "DM"
    
    print(f"Channel initialized: {guild_name} - #{channel_name} (Guild: {guild_id}, Channel: {channel_id})")
    
    embed = discord.Embed(
        title="✅ Channel Initialized!",
        description=f"This channel is now active for pinyin functionality.\n\n"
                   f"**Server:** {guild_name}\n"
                   f"**Channel:** #{channel_name}\n\n"
                   f"You can now send Chinese text and I'll respond with pinyin and Japanese translation!",
        color=0x00ff00
    )
    await ctx.send(embed=embed)

@bot.command(name='remove')
async def remove_channel(ctx):
    """Remove the current channel from pinyin functionality."""
    channel_id = ctx.channel.id
    guild_id = ctx.guild.id if ctx.guild else None
    
    # Create channel identifier
    channel_key = (guild_id, channel_id)
    
    if channel_key not in active_channels:
        await ctx.send(f"❌ This channel is not initialized for pinyin functionality!")
        return
    
    # Remove channel from active channels
    active_channels.remove(channel_key)
    
    # Save to file
    save_active_channels()
    
    guild_name = ctx.guild.name if ctx.guild else "DM"
    channel_name = ctx.channel.name if hasattr(ctx.channel, 'name') else "DM"
    
    print(f"Channel removed: {guild_name} - #{channel_name} (Guild: {guild_id}, Channel: {channel_id})")
    
    embed = discord.Embed(
        title="🗑️ Channel Removed!",
        description=f"This channel has been removed from pinyin functionality.\n\n"
                   f"**Server:** {guild_name}\n"
                   f"**Channel:** #{channel_name}\n\n"
                   f"Use `!init` to re-enable pinyin functionality in this channel.",
        color=0xff6b6b
    )
    await ctx.send(embed=embed)

@bot.command(name='status')
async def status(ctx):
    """Show the status of active channels."""
    if not active_channels:
        embed = discord.Embed(
            title="📊 Pinyin Bot Status",
            description="No channels are currently active for pinyin functionality.\n\nUse `!init` in any channel to activate it!",
            color=0xffa500
        )
        await ctx.send(embed=embed)
        return
    
    # Build status message
    status_lines = []
    for guild_id, channel_id in active_channels:
        try:
            guild = bot.get_guild(guild_id) if guild_id else None
            channel = bot.get_channel(channel_id)
            
            guild_name = guild.name if guild else "DM"
            channel_name = channel.name if channel and hasattr(channel, 'name') else f"Channel {channel_id}"
            
            status_lines.append(f"• **{guild_name}** - #{channel_name}")
        except Exception as e:
            status_lines.append(f"• Unknown Channel (ID: {channel_id})")
    
    embed = discord.Embed(
        title="📊 Pinyin Bot Status",
        description=f"**Active Channels ({len(active_channels)}):**\n\n" + "\n".join(status_lines),
        color=0x4CAF50
    )
    await ctx.send(embed=embed)

@bot.command(name='backup')
async def backup_channels(ctx):
    """Create a backup of active channels (Admin only)."""
    # Check if user has admin permissions
    if not ctx.author.guild_permissions.administrator:
        await ctx.send("❌ You need administrator permissions to use this command.")
        return
    
    try:
        backup_filename = f'channels_backup_{discord.utils.utcnow().strftime("%Y%m%d_%H%M%S")}.json'
        
        data = {
            'channels': [list(channel) for channel in active_channels],
            'backup_date': discord.utils.utcnow().isoformat(),
            'total_channels': len(active_channels)
        }
        
        with open(backup_filename, 'w') as f:
            json.dump(data, f, indent=2)
        
        embed = discord.Embed(
            title="💾 Backup Created!",
            description=f"Successfully created backup with {len(active_channels)} channels.\n\n"
                       f"**Backup file:** `{backup_filename}`",
            color=0x00ff00
        )
        await ctx.send(embed=embed)
        
    except Exception as e:
        embed = discord.Embed(
            title="❌ Backup Failed!",
            description=f"Error creating backup: {str(e)}",
            color=0xff0000
        )
        await ctx.send(embed=embed)

@bot.command(name='help')
async def help_command(ctx):
    """Show help information."""
    embed = discord.Embed(
        title="🤖 Pinyin Bot Help",
        description="I help you learn Chinese by providing pinyin and Japanese translations!",
        color=0x3498db
    )
    
    embed.add_field(
        name="📌 Setup Commands",
        value="`!init` - Initialize current channel for pinyin functionality\n"
              "`!remove` - Remove current channel from pinyin functionality\n"
              "`!status` - Show all active channels\n"
              "`!backup` - Create backup of active channels (Admin only)",
        inline=False
    )
    
    embed.add_field(
        name="🎯 How to Use",
        value="1. Run `!init` in any channel\n"
              "2. Send Chinese text in that channel\n"
              "3. I'll reply with pinyin and Japanese translation!\n"
              "4. Works across multiple servers and channels",
        inline=False
    )
    
    embed.add_field(
        name="✨ Features",
        value="• Pinyin with tone marks\n"
              "• Japanese translation\n"
              "• Multi-line text support\n"
              "• Beautiful image output\n"
              "• Persistent channel memory\n"
              "• Cross-server support",
        inline=False
    )
    
    await ctx.send(embed=embed)

@bot.event
async def on_message(message):
    # Process commands first
    await bot.process_commands(message)
    
    # Ignore messages from the bot itself
    if message.author == bot.user:
        return
    
    # Check if message starts with command prefix
    if message.content.startswith(bot.command_prefix):
        return
    
    # Check if current channel is active
    channel_id = message.channel.id
    guild_id = message.guild.id if message.guild else None
    channel_key = (guild_id, channel_id)
    
    if channel_key not in active_channels:
        return
    
    # Skip if message is empty or only whitespace
    if not message.content.strip():
        return
    
    try:
        # Split message by lines and process each line
        lines = message.content.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:  # Skip empty lines
                continue
                
            # Create image for this line
            image_buffer = create_image(line)
            
            if image_buffer:
                # Convert buffer to discord.File
                file = discord.File(image_buffer, filename=f'pinyin_{line[:10]}.png')
                
                # Reply to the original message with the image
                await message.reply(file=file)
            else:
                await message.reply(f"Sorry, couldn't process: {line}")
                
    except Exception as e:
        print(f"Error processing message: {e}")
        await message.reply("Sorry, there was an error processing your message.")

def run_flask():
    app.run(host='0.0.0.0', port=7860)

def run_bot():
    # Get Discord token from environment variable
    token = os.getenv('DISCORD_TOKEN')
    if not token:
        print("ERROR: DISCORD_TOKEN environment variable not set!")
        return
    
    try:
        bot.run(token)
    except Exception as e:
        print(f"Error running bot: {e}")

if __name__ == "__main__":
    # Start Flask server in a separate thread for Hugging Face Spaces health check
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    
    # Run the Discord bot
    run_bot()