import discord
from discord.ext import commands
import matplotlib.pyplot as plt
from pypinyin import pinyin, Style
import anthropic
import io
import os
import asyncio
import threading
import json
from flask import Flask
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.font_manager as fm
import re
from google.cloud import firestore
from google.oauth2 import service_account
from gtts import gTTS
from pydub import AudioSegment
import tempfile
from PIL import Image
import io
import time
import aiohttp

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

# Firestore setup - NO FALLBACK, MUST WORK
def init_firestore():
    """Initialize Firestore client - REQUIRED, no fallback."""
    print("🔥 Initializing Firestore connection...")
    
    # Try to get credentials from environment variable (JSON string)
    creds_json = os.getenv('GOOGLE_CLOUD_CREDENTIALS')
    if creds_json:
        print("📋 Found GOOGLE_CLOUD_CREDENTIALS environment variable")
        try:
            # Parse JSON string and create credentials
            creds_dict = json.loads(creds_json)
            print(f"📝 Parsed credentials for project: {creds_dict.get('project_id', 'UNKNOWN')}")
            credentials = service_account.Credentials.from_service_account_info(creds_dict)
            db = firestore.Client(database='pinyinbotchannels', credentials=credentials, project=creds_dict.get('project_id'))
            print("✅ Firestore initialized with credentials from environment variable")
            
            # Test connection by trying to access a collection
            try:
                test_ref = db.collection('connection_test').document('test')
                test_ref.set({'test': True, 'timestamp': firestore.SERVER_TIMESTAMP})
                print("✅ Firestore connection test successful - can write to database")
                test_ref.delete()  # Clean up test document
                return db
            except Exception as test_error:
                print(f"❌ Firestore connection test FAILED: {test_error}")
                raise Exception(f"Firestore connection test failed: {test_error}")
            
        except json.JSONDecodeError as json_error:
            print(f"❌ GOOGLE_CLOUD_CREDENTIALS is not valid JSON: {json_error}")
            raise Exception(f"Invalid GOOGLE_CLOUD_CREDENTIALS JSON: {json_error}")
        except Exception as creds_error:
            print(f"❌ Error creating Firestore credentials: {creds_error}")
            raise Exception(f"Firestore credentials error: {creds_error}")
    
    # Try service account key file
    key_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
    if key_path:
        print(f"📁 Found GOOGLE_APPLICATION_CREDENTIALS: {key_path}")
        if not os.path.exists(key_path):
            print(f"❌ Service account key file does not exist: {key_path}")
            raise FileNotFoundError(f"Service account key file not found: {key_path}")
        
        try:
            db = firestore.Client.from_service_account_json(key_path)
            print("✅ Firestore initialized with service account key file")
            
            # Test connection
            try:
                test_ref = db.collection('connection_test').document('test')
                test_ref.set({'test': True, 'timestamp': firestore.SERVER_TIMESTAMP})
                print("✅ Firestore connection test successful - can write to database")
                test_ref.delete()  # Clean up test document
                return db
            except Exception as test_error:
                print(f"❌ Firestore connection test FAILED: {test_error}")
                raise Exception(f"Firestore connection test failed: {test_error}")
                
        except Exception as key_error:
            print(f"❌ Error initializing Firestore with key file: {key_error}")
            raise Exception(f"Firestore key file error: {key_error}")
    
    # Try default credentials (for Google Cloud environments)
    print("🔍 Trying default Google Cloud credentials...")
    try:
        db = firestore.Client()
        print("✅ Firestore initialized with default credentials")
        
        # Test connection
        try:
            test_ref = db.collection('connection_test').document('test')
            test_ref.set({'test': True, 'timestamp': firestore.SERVER_TIMESTAMP})
            print("✅ Firestore connection test successful - can write to database")
            test_ref.delete()  # Clean up test document
            return db
        except Exception as test_error:
            print(f"❌ Firestore connection test FAILED: {test_error}")
            raise Exception(f"Firestore connection test failed: {test_error}")
            
    except Exception as default_error:
        print(f"❌ Error with default credentials: {default_error}")
    
    # NO FALLBACK - RAISE ERROR
    error_msg = """
❌ FIRESTORE CONNECTION FAILED ❌

No valid Firestore credentials found! You must set up one of:

1. GOOGLE_CLOUD_CREDENTIALS environment variable (recommended for Hugging Face)
   - Set this to the complete JSON content of your service account key

2. GOOGLE_APPLICATION_CREDENTIALS environment variable
   - Set this to the path of your service account key file

3. Default Google Cloud credentials (for GCP environments)

SETUP INSTRUCTIONS:
1. Go to Firebase Console: https://console.firebase.google.com/
2. Create a project and enable Firestore
3. Generate a service account key (JSON)
4. Add GOOGLE_CLOUD_CREDENTIALS secret with the JSON content

Current environment:
- GOOGLE_CLOUD_CREDENTIALS: {'SET' if creds_json else 'NOT SET'}
- GOOGLE_APPLICATION_CREDENTIALS: {key_path if key_path else 'NOT SET'}

Bot cannot start without Firestore connection!
"""
    print(error_msg)
    raise Exception("Firestore connection required but failed to initialize")

# Initialize Firestore - REQUIRED
print("🚀 Starting Firestore initialization...")
db = init_firestore()
print("🎉 Firestore successfully connected!")

# Store active channels (guild_id, channel_id) pairs
active_channels = set()
CHANNELS_COLLECTION = 'active_channels'
CHANNELS_DOCUMENT = 'channels_data'

async def load_active_channels():
    """Load active channels from Firestore - REQUIRED."""
    global active_channels

    print("📥 Loading active channels from Firestore...")

    try:
        # Load from Firestore
        doc_ref = db.collection(CHANNELS_COLLECTION).document(CHANNELS_DOCUMENT)
        doc = doc_ref.get()

        if doc.exists:
            data = doc.to_dict()
            channels_data = data.get('channels', [])

            # Convert list of dicts back to set of tuples
            active_channels = set(
                (channel.get('guild_id'), channel.get('channel_id'))
                for channel in channels_data
                if channel is not None and 'guild_id' in channel and 'channel_id' in channel
            )

            print(f"✅ Loaded {len(active_channels)} active channels from Firestore")
        else:
            active_channels = set()
            print("📝 No existing channels document in Firestore, starting with empty channel list")
            # Create initial empty document
            doc_ref.set({
                'channels': [],
                'last_updated': firestore.SERVER_TIMESTAMP,
                'total_channels': 0
            })
            print("✅ Created initial empty channels document in Firestore")

    except Exception as e:
        print(f"❌ CRITICAL ERROR loading active channels from Firestore: {e}")
        raise Exception(f"Failed to load channels from Firestore: {e}")


async def save_active_channels():
    """Save active channels to Firestore - REQUIRED."""

    print(f"💾 Saving {len(active_channels)} active channels to Firestore...")

    try:
        # Save to Firestore
        doc_ref = db.collection(CHANNELS_COLLECTION).document(CHANNELS_DOCUMENT)

        data = {
            'channels': [
                {'guild_id': channel[0], 'channel_id': channel[1]}
                for channel in active_channels
            ],
            'last_updated': firestore.SERVER_TIMESTAMP,
            'total_channels': len(active_channels)
        }

        doc_ref.set(data)
        print(f"✅ Successfully saved {len(active_channels)} active channels to Firestore")

    except Exception as e:
        print(f"❌ CRITICAL ERROR saving active channels to Firestore: {e}")
        raise Exception(f"Failed to save channels to Firestore: {e}")


async def create_backup():
    """Create a backup of active channels in Firestore - REQUIRED."""
    
    print("🔄 Creating Firestore backup...")
    
    try:
        # Create backup collection with timestamp
        backup_id = discord.utils.utcnow().strftime("%Y%m%d_%H%M%S")
        backup_ref = db.collection('channel_backups').document(backup_id)
        
        data = {
            'channels': [list(channel) for channel in active_channels],
            'backup_date': firestore.SERVER_TIMESTAMP,
            'total_channels': len(active_channels)
        }
        
        backup_ref.set(data)
        print(f"✅ Successfully created backup {backup_id} with {len(active_channels)} channels")
        return backup_id
        
    except Exception as e:
        print(f"❌ CRITICAL ERROR creating Firestore backup: {e}")
        raise Exception(f"Failed to create Firestore backup: {e}")

def is_chinese_char(char):
    """Check if a character is Chinese."""
    return '\u4e00' <= char <= '\u9fff'

def has_chinese_content(text):
    """Check if text contains Chinese characters."""
    return any(is_chinese_char(char) for char in text)

def tokenize_text(text):
    """Tokenize text into segments of Chinese characters and non-Chinese segments."""
    segments = []
    current_segment = ""
    is_current_chinese = None
    
    for char in text:
        char_is_chinese = is_chinese_char(char)
        
        if is_current_chinese is None:
            # First character
            current_segment = char
            is_current_chinese = char_is_chinese
        elif char_is_chinese == is_current_chinese:
            # Same type as current segment
            current_segment += char
        else:
            # Different type, start new segment
            segments.append({
                'text': current_segment,
                'is_chinese': is_current_chinese
            })
            current_segment = char
            is_current_chinese = char_is_chinese
    
    # Add the last segment
    if current_segment:
        segments.append({
            'text': current_segment,
            'is_chinese': is_current_chinese
        })
    
    return segments

def get_pinyin_for_segments(segments):
    """Get pinyin for segments, only process Chinese segments."""
    result_segments = []
    
    for segment in segments:
        if segment['is_chinese']:
            # Process Chinese characters
            pinyin_list = []
            for char in segment['text']:
                py = pinyin(char, style=Style.TONE)
                if py and py[0]:
                    pinyin_list.append(py[0][0].replace("u:", "ü"))
                else:
                    pinyin_list.append(char)
            
            result_segments.append({
                'original': segment['text'],
                'pinyin': ' '.join(pinyin_list),
                'is_chinese': True
            })
        else:
            # Non-Chinese text, keep as is
            result_segments.append({
                'original': segment['text'],
                'pinyin': segment['text'],
                'is_chinese': False
            })
    
    return result_segments

def translate_chinese_to_japanese(text):
    try:
        # Initialize Anthropic client
        client = anthropic.Anthropic(
            api_key=os.getenv('ANTHROPIC_API_KEY')
        )
        
        # Create translation prompt
        prompt = f"Translate the following Chinese text to Japanese. Only return the Japanese translation, no explanations: {text}"
        
        # Get translation from Claude
        message = client.messages.create(
            model="claude-3-haiku-20240307",  # Using Haiku for cost efficiency
            max_tokens=1000,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        return message.content[0].text.strip()
        
    except Exception as e:
        print(f"Translation error: {e}")
        return "Translation failed"

def create_image(text):
    """Create image for single line of text with proper mixed language handling."""
    if not text.strip():
        return None
    
    try:
        # Check if text contains Chinese
        if not has_chinese_content(text):
            return None
        
        # Tokenize text into segments
        segments = tokenize_text(text.strip())
        processed_segments = get_pinyin_for_segments(segments)
        
        # Get Japanese translation for the entire text
        japanese_translation = translate_chinese_to_japanese(text.strip())
        
        # Calculate figure dimensions based on text length
        text_length = len(text.strip())
        fig_width = max(text_length * 0.6, 8)
        fig_height = 6  # Fixed height for single line
        
        fig, ax = plt.subplots(figsize=(fig_width, fig_height))
        
        # Find suitable fonts
        cjk_font = fm.FontProperties(family=['Noto Sans CJK SC', 'Noto Sans CJK JP'])
        regular_font = fm.FontProperties(family=['DejaVu Sans', 'Arial'])
        
        # Create pinyin line by combining all segments
        pinyin_line = ''.join(seg['pinyin'] for seg in processed_segments)
        original_line = text.strip()
        
        # Center everything vertically
        y_positions = {
            'pinyin': 0.7,    # Top
            'original': 0.5,  # Middle
            'japanese': 0.3   # Bottom
        }
        
        # Draw pinyin (top line)
        ax.text(0.5, y_positions['pinyin'], pinyin_line, 
               fontsize=16, ha='center', va='center', 
               fontproperties=cjk_font, weight='normal')
        
        # Draw original text (middle line, bold)
        ax.text(0.5, y_positions['original'], original_line, 
               fontsize=22, ha='center', va='center', 
               fontproperties=cjk_font, weight='bold')
        
        # Draw Japanese translation (bottom line)
        ax.text(0.5, y_positions['japanese'], japanese_translation, 
               fontsize=14, ha='center', va='center', 
               color='blue', fontproperties=cjk_font)
        
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')
        
        # Save to bytes buffer with tight layout
        buf = io.BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight', dpi=300, 
           facecolor='white', edgecolor='none', pad_inches=0.3,
           metadata={'chinese_text': original_line})
           
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
    print(f'🤖 {bot.user} has connected to Discord!')
    print(f'🏠 Bot is in {len(bot.guilds)} guilds')
    
    # Load active channels from Firestore
    try:
        await load_active_channels()
        print(f"📋 Successfully loaded channel data")
    except Exception as e:
        print(f"❌ CRITICAL: Failed to load channels: {e}")
        raise e
    
    # Clean up invalid channels (channels that no longer exist)
    try:
        await cleanup_invalid_channels()
        print(f"🧹 Channel cleanup completed")
    except Exception as e:
        print(f"❌ CRITICAL: Failed to cleanup channels: {e}")
        raise e

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
        
        print(f"🧹 Cleaned up {len(invalid_channels)} invalid channels")
        try:
            await save_active_channels()
            print(f"✅ Successfully saved cleanup results to Firestore")
        except Exception as e:
            print(f"❌ CRITICAL: Failed to save cleanup results: {e}")
            raise e

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
    
    # Save to Firestore
    try:
        await save_active_channels()
        print(f"✅ Successfully saved new channel to Firestore")
    except Exception as e:
        print(f"❌ CRITICAL: Failed to save channel: {e}")
        # Remove from memory since save failed
        active_channels.discard(channel_key)
        await ctx.send(f"❌ **Critical Error**: Failed to save channel to Firestore!\n```{str(e)}```")
        return
    
    guild_name = ctx.guild.name if ctx.guild else "DM"
    channel_name = ctx.channel.name if hasattr(ctx.channel, 'name') else "DM"
    
    print(f"Channel initialized: {guild_name} - #{channel_name} (Guild: {guild_id}, Channel: {channel_id})")
    
    embed = discord.Embed(
        title="✅ Channel Initialized!",
        description=f"This channel is now active for pinyin functionality.\n\n"
                   f"**Server:** {guild_name}\n"
                   f"**Channel:** #{channel_name}\n"
                   f"**Storage:** Firestore ☁️\n\n"
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
    
    # Save to Firestore
    try:
        await save_active_channels()
        print(f"✅ Successfully removed channel from Firestore")
    except Exception as e:
        print(f"❌ CRITICAL: Failed to remove channel: {e}")
        # Add back to memory since save failed
        active_channels.add(channel_key)
        await ctx.send(f"❌ **Critical Error**: Failed to remove channel from Firestore!\n```{str(e)}```")
        return
    
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
            description=f"No channels are currently active for pinyin functionality.\n\n"
                       f"**Storage:** Firestore ☁️\n\n"
                       f"Use `!init` in any channel to activate it!",
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
        description=f"**Active Channels ({len(active_channels)}):**\n\n" + "\n".join(status_lines) + f"\n\n**Storage:** Firestore ☁️",
        color=0x4CAF50
    )
    await ctx.send(embed=embed)

@bot.command(name='backup')
async def backup_channels(ctx):
    """Create a backup of active channels."""
    # Check if user has admin permissions
    if not ctx.author.guild_permissions.administrator:
        await ctx.send("❌ You need administrator permissions to use this command.")
        return
    
    try:
        # Create Firestore backup
        backup_id = await create_backup()
        embed = discord.Embed(
            title="☁️ Firestore Backup Created!",
            description=f"Successfully created backup with {len(active_channels)} channels.\n\n"
                       f"**Backup ID:** `{backup_id}`\n"
                       f"**Storage:** Firestore ☁️",
            color=0x00ff00
        )
        await ctx.send(embed=embed)
        
    except Exception as e:
        print(f"❌ CRITICAL: Backup failed: {e}")
        embed = discord.Embed(
            title="❌ Backup Failed!",
            description=f"**Critical Error**: Failed to create Firestore backup!\n```{str(e)}```",
            color=0xff0000
        )
        await ctx.send(embed=embed)

@bot.command(name='help')
async def help_command(ctx):
    """Show help information."""
    
    embed = discord.Embed(
        title="🤖 Pinyin Bot Help",
        description=f"I help you learn Chinese by providing pinyin and Japanese translations!\n\n**Storage:** Firestore ☁️ (Required)",
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
              "4. Each line is processed separately\n"
              "5. Works with mixed Chinese/English text",
        inline=False
    )
    
    embed.add_field(
        name="✨ Features",
        value="• Pinyin with tone marks\n"
              "• Japanese translation\n"
              "• Mixed Chinese/English text support\n"
              "• Proper punctuation handling\n"
              "• Beautiful centered image output\n"
              "• Cloud storage with Firestore (REQUIRED)\n"
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
    
    # Check if message contains Chinese characters
    if not has_chinese_content(message.content):
        return
    
    try:
        # Split message by lines and process each line separately
        lines = [line.strip() for line in message.content.strip().split('\n') if line.strip()]
        
        for line in lines:
            if has_chinese_content(line):
                # Create image for this line
                image_buffer = create_image(line)
                
                if image_buffer:
                    # Convert buffer to discord.File
                    file = discord.File(image_buffer, filename='pinyin_translation.png')
                    
                    # Create view with button
                    view = AudioButtonView()

                    # Reply to the original message with the image and button
                    await message.reply(file=file, view=view)
                    
                    # Small delay between images to avoid rate limiting
                    if len(lines) > 1:
                        await asyncio.sleep(0.5)
                else:
                    await message.reply(f"Sorry, couldn't process: {line}")
                
    except Exception as e:
        print(f"Error processing message: {e}")
        await message.reply("Sorry, there was an error processing your message.")


class AudioButtonView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)  # No timeout since we're reading from image
    
    @discord.ui.button(label='🔊 Play Audio', style=discord.ButtonStyle.primary)
    async def play_audio(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        
        try:
            # Get the message that contains this view (the bot's reply with the image)
            message = interaction.message
            
            # Check if message has attachments
            if not message.attachments:
                await interaction.followup.send("No image found to extract text from.", ephemeral=True)
                return
            
            # Get the first attachment (should be our PNG image)
            attachment = message.attachments[0]
            
            # Download the image bytes
            image_bytes = await attachment.read()
            
            # Extract Chinese text from PNG metadata
            try:
                img = Image.open(io.BytesIO(image_bytes))
                chinese_text = img.info.get('chinese_text', '')
                
                if not chinese_text:
                    await interaction.followup.send("Could not find Chinese text in image metadata.", ephemeral=True)
                    return
                
            except Exception as e:
                print(f"Error reading image metadata: {e}")
                await interaction.followup.send("Could not read image metadata.", ephemeral=True)
                return
            
            # Generate audio using the extracted Chinese text
            audio_path = create_audio(chinese_text)
            
            if audio_path:
                try:
                    # Send audio file
                    with open(audio_path, 'rb') as audio_file:
                        discord_file = discord.File(audio_file, filename='chinese_audio.mp3')
                        await interaction.followup.send(file=discord_file)
                    
                    # Clean up temporary file
                    os.unlink(audio_path)
                    
                except Exception as e:
                    await interaction.followup.send("Sorry, couldn't generate audio.", ephemeral=True)
            else:
                await interaction.followup.send("Sorry, couldn't generate audio.", ephemeral=True)
                
        except Exception as e:
            print(f"Error in play_audio: {e}")
            await interaction.followup.send("Sorry, there was an error generating audio.", ephemeral=True)


def create_audio(text):
    """Create audio file for Chinese text."""
    try:
        # Extract only Chinese characters for TTS
        chinese_only = ''.join(char for char in text if is_chinese_char(char))
        
        if not chinese_only:
            return None
            
        # Create TTS audio
        tts = gTTS(text=chinese_only, lang='zh-cn', slow=False)
        
        # Save to temporary file
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_file:
            tts.save(temp_file.name)
            return temp_file.name
            
    except Exception as e:
        print(f"Error creating audio: {e}")
        return None


def run_flask():
    app.run(host='0.0.0.0', port=7860)

def run_bot():
    # Get Discord token from environment variable
    token = os.getenv('DISCORD_TOKEN')
    if not token:
        error_msg = """
❌ DISCORD TOKEN MISSING ❌

DISCORD_TOKEN environment variable not set!

Please set your Discord bot token in the environment variables.
"""
        print(error_msg)
        raise Exception("DISCORD_TOKEN environment variable not set!")
    
    max_retries = 5
    retry_delay = 10

    for attempt in range(max_retries):
        try:
            print(f"🚀 Starting Discord bot (attempt {attempt + 1}/{max_retries})...")
            bot.run(token)
            break
        except aiohttp.client_exceptions.ClientConnectorDNSError as e:
            print(f"❌ DNS error on attempt {attempt + 1}: {e}")
            if attempt < max_retries - 1:
                print(f"⏳ Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)  # Use time.sleep, not await
                retry_delay *= 2  # Exponential backoff
            else:
                raise e
        except Exception as e:
            print(f"❌ CRITICAL ERROR running bot: {e}")
            raise e
    

    anthropic_key = os.getenv('ANTHROPIC_API_KEY')
    if not anthropic_key:
        error_msg = """
    ❌ ANTHROPIC API KEY MISSING ❌

    ANTHROPIC_API_KEY environment variable not set!

    Please set your Anthropic API key in the environment variables.
    """
        print(error_msg)
        raise Exception("ANTHROPIC_API_KEY environment variable not set!")

if __name__ == "__main__":
    print("🔥 Starting Chinese Pinyin Discord Bot (Firestore Required)")
    
    # Start Flask server in a separate thread for Hugging Face Spaces health check
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    print("🌐 Flask health check server started")
    
    # Test network connectivity before starting bot
    try:
        import socket
        socket.gethostbyname('discord.com')
        print("✅ Network connectivity to discord.com confirmed")
    except socket.gaierror:
        print("❌ Cannot resolve discord.com - network connectivity issue")
        print("⏳ Waiting 30 seconds before retry...")
        time.sleep(30)  # Use time.sleep instead of await asyncio.sleep
        # Try again or raise exception

    # Run the Discord bot
    run_bot()