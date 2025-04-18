import os
import math
import logging
from pyrogram import Client, filters, idle
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from mega import Mega
from config import Config

# إعداد تسجيل الدخول لحساب Mega
mega = Mega()
m = mega.login(Config.MEGA_EMAIL, Config.MEGA_PASSWORD)

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
        file_info = m.get_public_url_info(url)
    except Exception as e:
        await status.edit(f"❌ خطأ أثناء الوصول للرابط: {e}")
        return

    # حالة رابط مجلد
    if file_info['type'] == 'folder':
        files = m.download_url(url, DOWNLOAD_DIR)
        await status.edit("📁 تم تحميل المجلد، جاري الإرسال...")
        for file_path in files:
            try:
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
            except Exception as e:
                await bot.send_message(message.chat.id, f"❌ فشل في إرسال {file_path}: {e}")
        await status.delete()

    # حالة رابط ملف مفرد
    else:
        try:
            file_path = m.download_url(url, DOWNLOAD_DIR)
        except Exception as e:
            await status.edit(f"❌ خطأ أثناء التحميل: {e}")
            return

        size_mb = os.path.getsize(file_path) / (1024 * 1024)
        await status.edit(f"✅ تم التحميل ({size_mb:.2f} MB)، جاري الرفع...")

        try:
            if os.path.getsize(file_path) > CHUNK_SIZE:
                parts = split_file(file_path)
                for i, part in enumerate(parts):
                    caption = f"📦 جزء {i+1} من {len(parts)}\n📤 تم بواسطة البوت @Z_Bots"
                    await bot.send_document(message.chat.id, document=part, caption=caption)
                    os.remove(part)
            else:
                caption = f"📤 تم بواسطة البوت @صصص"
                await bot.send_document(message.chat.id, document=file_path, caption=caption)
            await status.delete()
        except Exception as e:
            await status.edit(f"❌ فشل أثناء الرفع: {e}")

        os.remove(file_path)

bot.start()
idle()
