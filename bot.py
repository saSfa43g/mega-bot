import os
import math
import logging
from pyrogram import Client, filters, idle
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from megadownloader import MegaDownloader
from config import Config

# إعداد بوت تيليجرام
bot = Client(
    "MegaNzBot",
    api_id=Config.API_ID,
    api_hash=Config.API_HASH,
    bot_token=Config.BOT_TOKEN,
)

# إعداد المجلد المؤقت للتحميل
DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# تقسيم الملف إلى أجزاء
CHUNK_SIZE_MB = 1900
CHUNK_SIZE = CHUNK_SIZE_MB * 1024 * 1024

def split_file(file_path):
    parts = []
    total_size = os.path.getsize(file_path)
    total_parts = math.ceil(total_size / CHUNK_SIZE)
    with open(file_path, 'rb') as f:
        for i in range(total_parts):
            part_name = f"{file_path}.part{i+1}"
            with open(part_name, 'wb') as chunk:
                chunk.write(f.read(CHUNK_SIZE))
            parts.append(part_name)
    return parts

@bot.on_message(filters.command("start") & filters.private)
async def start(_, message):
    user = message.from_user.mention
    await message.reply_text(
        f"""👋 أهلاً {user}،

أنا بوت لتحميل روابط MEGA.NZ ورفعها إلى تيليجرام 🧠
أرسل رابط ملف أو مجلد Mega.nz وسأتولى الباقي ✅""",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📢 قناتنا", url="https://t.me/صص")]
        ])
    )

@bot.on_message(filters.regex("https://mega.nz/") & filters.private)
async def handle_mega(_, message):
    url = message.text
    user = message.from_user.mention
    status = await message.reply("📥 جاري المعالجة...")

    try:
        # استخدام MegaDownloader
        mega = MegaDownloader()
        mega.download_url(url, DOWNLOAD_DIR)  # تحميل الملف أو المجلد
        
    except Exception as e:
        await status.edit(f"❌ خطأ أثناء الوصول للرابط: {e}")
        return

    # تحميل المجلدات أو الملفات باستخدام mega-downloader
    try:
        files = [os.path.join(DOWNLOAD_DIR, f) for f in os.listdir(DOWNLOAD_DIR)]
        for file_path in files:
            if os.path.getsize(file_path) > CHUNK_SIZE:
                parts = split_file(file_path)
                for i, part in enumerate(parts):
                    caption = f"📦 {os.path.basename(file_path)}\n📄 جزء {i+1} من {len(parts)}\n🧠 بواسطة @Z_Bots"
                    await bot.send_document(message.chat.id, document=part, caption=caption)
                    os.remove(part)
            else:
                caption = f"📄 {os.path.basename(file_path)}\n🧠 بواسطة @Z_Bots"
                await bot.send_document(message.chat.id, document=file_path, caption=caption)
            os.remove(file_path)
        await status.delete()
    except Exception as e:
        await status.edit(f"❌ خطأ أثناء تحميل الملفات: {e}")

bot.start()
idle()
