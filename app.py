import discord
from discord.ext import commands
import matplotlib.pyplot as plt
from pypinyin import pinyin, Style
from googletrans import Translator
import io
import os
import asyncio
import threading
from flask import Flask
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.font_manager as fm

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
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')

@bot.event
async def on_message(message):
    # Ignore messages from the bot itself
    if message.author == bot.user:
        return
    
    # Only respond in channels named "pinyin"
    if message.channel.name != 'pinyin':
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