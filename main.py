import discord
from discord.ext import commands
import asyncio
import aiohttp
import json
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from PIL import Image
import time
import tempfile
from pypinyin import pinyin, lazy_pinyin, Style
import html

# Bot setup
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Configuration
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
PINYIN_CHANNEL = os.getenv('PINYIN_CHANNEL', 'pinyin')

class PinyinTranslator:
    def __init__(self, api_key):
        self.api_key = api_key
        
    def generate_pinyin(self, chinese_text):
        """Generate pinyin for Chinese text"""
        try:
            # Get pinyin with tone marks
            pinyin_with_tones = pinyin(chinese_text, style=Style.TONE, heteronym=False)
            pinyin_text = ' '.join([item[0] for item in pinyin_with_tones])
            return pinyin_text
        except Exception as e:
            print(f"Error generating pinyin: {e}")
            return ""
            
    async def translate_to_japanese(self, text):
        """Translate Chinese text to Japanese using Google Translate API"""
        try:
            url = f"https://translation.googleapis.com/language/translate/v2?key={self.api_key}"
            
            payload = {
                "q": text,
                "source": "zh",
                "target": "ja",
                "format": "text"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data['data']['translations'][0]['translatedText']
                    else:
                        print(f"Translation API error: {response.status}")
                        return "Translation failed"
        except Exception as e:
            print(f"Error translating text: {e}")
            return "Translation error"
    
    def create_webpage_html(self, original_text, pinyin_text, japanese_text):
        """Create HTML page with the texts"""
        html_template = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Chinese Text Analysis</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            max-width: 800px;
            margin: 40px auto;
            padding: 30px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            box-sizing: border-box;
        }}
        
        .container {{
            background: rgba(255, 255, 255, 0.95);
            border-radius: 20px;
            padding: 40px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            backdrop-filter: blur(10px);
        }}
        
        h1 {{
            color: #2c3e50;
            text-align: center;
            margin-bottom: 40px;
            font-size: 2.5em;
            font-weight: 300;
            letter-spacing: -1px;
        }}
        
        .text-section {{
            margin-bottom: 30px;
            padding: 25px;
            border-radius: 15px;
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }}
        
        .text-section:hover {{
            transform: translateY(-5px);
            box-shadow: 0 15px 30px rgba(0,0,0,0.1);
        }}
        
        .original {{
            background: linear-gradient(135deg, #ff9a9e 0%, #fecfef 100%);
            border-left: 5px solid #e74c3c;
        }}
        
        .pinyin {{
            background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);
            border-left: 5px solid #3498db;
        }}
        
        .japanese {{
            background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%);
            border-left: 5px solid #f39c12;
        }}
        
        .label {{
            font-weight: 600;
            font-size: 1.1em;
            color: #2c3e50;
            margin-bottom: 10px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        
        .content {{
            font-size: 1.4em;
            line-height: 1.6;
            color: #34495e;
            word-wrap: break-word;
        }}
        
        .original .content {{
            font-size: 1.6em;
            font-weight: 500;
        }}
        
        .footer {{
            text-align: center;
            margin-top: 40px;
            color: #7f8c8d;
            font-style: italic;
        }}
        
        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(20px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
        
        .text-section {{
            animation: fadeIn 0.6s ease-out;
        }}
        
        .text-section:nth-child(2) {{ animation-delay: 0.1s; }}
        .text-section:nth-child(3) {{ animation-delay: 0.2s; }}
        .text-section:nth-child(4) {{ animation-delay: 0.3s; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>中文文本分析 / Chinese Text Analysis</h1>
        
        <div class="text-section original">
            <div class="label">Original Chinese / 原文</div>
            <div class="content">{html.escape(original_text)}</div>
        </div>
        
        <div class="text-section pinyin">
            <div class="label">Pinyin / 拼音</div>
            <div class="content">{html.escape(pinyin_text)}</div>
        </div>
        
        <div class="text-section japanese">
            <div class="label">Japanese Translation / 日本語訳</div>
            <div class="content">{html.escape(japanese_text)}</div>
        </div>
        
        <div class="footer">
            Generated by Discord Bot • {time.strftime('%Y-%m-%d %H:%M:%S')}
        </div>
    </div>
</body>
</html>
        """
        return html_template
    
    def render_html_to_image(self, html_content):
        """Render HTML to image using Selenium"""
        try:
            # Setup Chrome options for Docker
            options = Options()
            options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-gpu')
            options.add_argument('--window-size=1000,800')
            options.add_argument('--disable-web-security')
            options.add_argument('--allow-running-insecure-content')
            
            # Create webdriver
            driver = webdriver.Chrome(options=options)
            
            # Load HTML content
            data_uri = "data:text/html;charset=utf-8," + html_content
            driver.get(data_uri)
            
            # Wait for content to load
            time.sleep(3)
            
            # Create temporary file for screenshot
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
                screenshot_path = tmp_file.name
            
            # Take screenshot
            driver.save_screenshot(screenshot_path)
            driver.quit()
            
            # Convert to JPG for smaller file size
            img = Image.open(screenshot_path)
            jpg_path = screenshot_path.replace('.png', '.jpg')
            img.convert('RGB').save(jpg_path, quality=95, optimize=True)
            
            # Clean up PNG file
            os.unlink(screenshot_path)
            
            return jpg_path
            
        except Exception as e:
            print(f"Error rendering HTML to image: {e}")
            if 'driver' in locals():
                driver.quit()
            return None

# Initialize translator
translator = PinyinTranslator(GOOGLE_API_KEY)

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    print(f'Bot is ready to process messages in #{PINYIN_CHANNEL} channel')

@bot.event
async def on_message(message):
    # Don't respond to bot's own messages
    if message.author == bot.user:
        return
    
    # Check if message is in the pinyin channel
    if message.channel.name != PINYIN_CHANNEL:
        await bot.process_commands(message)
        return
    
    # Check if message contains Chinese characters
    if not any('\u4e00' <= char <= '\u9fff' for char in message.content):
        await bot.process_commands(message)
        return
    
    try:
        # Show typing indicator
        async with message.channel.typing():
            print(f"Processing message: {message.content}")
            
            # Generate pinyin
            pinyin_text = translator.generate_pinyin(message.content)
            
            # Translate to Japanese
            japanese_text = await translator.translate_to_japanese(message.content)
            
            # Create HTML page
            html_content = translator.create_webpage_html(
                message.content, 
                pinyin_text, 
                japanese_text
            )
            
            # Render to image
            image_path = translator.render_html_to_image(html_content)
            
            if image_path and os.path.exists(image_path):
                # Send image as reply
                with open(image_path, 'rb') as f:
                    discord_file = discord.File(f, filename='chinese_analysis.jpg')
                    await message.reply(file=discord_file, mention_author=False)
                
                # Clean up temporary file
                os.unlink(image_path)
                print("Image sent successfully")
            else:
                await message.reply("Sorry, I couldn't generate the image. Please try again.")
                
    except Exception as e:
        print(f"Error processing message: {e}")
        await message.reply("An error occurred while processing your message.")
    
    # Process other commands
    await bot.process_commands(message)

@bot.command(name='test')
async def test_command(ctx, *, text=None):
    """Test command to manually process Chinese text"""
    if not text:
        await ctx.send("Please provide Chinese text to test. Usage: `!test 你好世界`")
        return
    
    # Check if text contains Chinese characters
    if not any('\u4e00' <= char <= '\u9fff' for char in text):
        await ctx.send("Please provide Chinese text containing Chinese characters.")
        return
    
    try:
        async with ctx.typing():
            # Generate pinyin
            pinyin_text = translator.generate_pinyin(text)
            
            # Translate to Japanese
            japanese_text = await translator.translate_to_japanese(text)
            
            # Create HTML page
            html_content = translator.create_webpage_html(text, pinyin_text, japanese_text)
            
            # Render to image
            image_path = translator.render_html_to_image(html_content)
            
            if image_path and os.path.exists(image_path):
                with open(image_path, 'rb') as f:
                    discord_file = discord.File(f, filename='chinese_analysis.jpg')
                    await ctx.send(file=discord_file)
                
                os.unlink(image_path)
            else:
                await ctx.send("Sorry, I couldn't generate the image.")
                
    except Exception as e:
        print(f"Error in test command: {e}")
        await ctx.send("An error occurred while processing the text.")

@bot.command(name='help_pinyin')
async def help_command(ctx):
    """Show help information"""
    help_text = """
**Chinese Pinyin Bot Help**

🎯 **Automatic Processing:**
- Send Chinese text in the `#{PINYIN_CHANNEL}` channel
- Bot will automatically generate pinyin and Japanese translation
- Returns a beautiful image with all three texts

🔧 **Commands:**
- `!test <chinese text>` - Test the bot with Chinese text
- `!help_pinyin` - Show this help message

📝 **Example:**
Send "你好世界" in #{PINYIN_CHANNEL} and get pinyin + Japanese translation!
    """.format(PINYIN_CHANNEL=PINYIN_CHANNEL)
    
    await ctx.send(help_text)

if __name__ == "__main__":
    if not DISCORD_TOKEN:
        print("Error: DISCORD_TOKEN environment variable not set")
        exit(1)
    
    if not GOOGLE_API_KEY:
        print("Error: GOOGLE_API_KEY environment variable not set")
        exit(1)
    
    bot.run(DISCORD_TOKEN)