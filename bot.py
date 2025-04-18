import os
import math
import subprocess
from pyrogram import Client, filters, idle
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import Config

bot = Client(
    "MegaBot",
    api_id=Config.API_ID,
    api_hash=Config.API_HASH,
    bot_token=Config.BOT_TOKEN,
)

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

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

def download_with_megatools(url, download_dir):
    try:
        result = subprocess.run(
            ["megadl", "--path", download_dir, url],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True
        )
        return True, result.stdout.decode()
    except subprocess.CalledProcessError as e:
        return False, e.stderr.decode()

@bot.on_message(filters.command("start") & filters.private)
async def start(_, message):
    user = message.from_user.mention
    await message.reply_text(
        f"""👋 أهلاً {user}،

أنا بوت لتحميل روابط MEGA.NZ ورفعها إلى تيليجرام 🧠
أرسل رابط ملف Mega.nz وسأتولى الباقي ✅""",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📢 قناتنا", url="https://t.me/صص")]
        ])
    )

@bot.on_message(filters.regex("https://mega.nz/") & filters.private)
async def handle_mega(_, message):
    url = message.text
    status = await message.reply("📥 جاري التحميل...")

    success, output = download_with_megatools(url, DOWNLOAD_DIR)
    if not success:
        await status.edit(f"❌ فشل التحميل:\n{output}")
        return

    files = [os.path.join(DOWNLOAD_DIR, f) for f in os.listdir(DOWNLOAD_DIR)]
    try:
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
        await status.edit(f"❌ خطأ أثناء الإرسال: {e}")

bot.start()
idle()
