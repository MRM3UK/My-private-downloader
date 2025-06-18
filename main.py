import os
import yt_dlp
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from flask import Flask
from threading import Thread
import re
import logging

# === CONFIG ===
TOKEN = os.getenv("8052121647:AAGyRuu7gTo4zfcNOMvLifNzsRtCY-tQlig")  # Use environment variable
DOWNLOAD_DIR = "downloads"
COOKIE_FILE = "cookies.txt"
BOT_USERNAME = "@DownloaderReelbot"

# Create directories and files
os.makedirs(DOWNLOAD_DIR, exist_ok=True)
if not os.path.exists(COOKIE_FILE):
    open(COOKIE_FILE, 'a').close()  # Create empty cookies file if missing

# === Logging ===
logging.basicConfig(level=logging.INFO)

# === Keep-alive with Flask ===
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is online!"

def run():
    port = int(os.getenv("PORT", 8080))  # Use Render's PORT or default to 8080
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    Thread(target=run, daemon=True).start()

# === Clean caption (escape MarkdownV2) ===
def clean_caption(text):
    return re.sub(r'([_*`\[()\]~\>#+\-|=|{}.!\\])', r'\\\1', text)

# === Format final caption ===
def build_caption(insta_username, title, caption, url):
    caption = clean_caption(caption.strip() if caption else title)
    spoiler_caption = f"||{caption}||"
    final_caption = (
        f"Video by _{insta_username}_\n\n"
        f"{spoiler_caption}\n\n"
        f"{url}\n\n"
        f"{BOT_USERNAME}"
    )
    return final_caption[:1024]

# === Download video ===
def download_video(url):
    ydl_opts = {
        'format': 'best[filesize<50M]',  # Limit to 50MB for Telegram
        'cookiefile': COOKIE_FILE,
        'outtmpl': f"{DOWNLOAD_DIR}/%(title).40s.%(ext)s",
        'quiet': True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        title = info.get('title', '')
        desc = info.get('description', '') or info.get('caption', '')
        uploader = info.get('uploader', 'unknown')
        return ydl.prepare_filename(info), title, desc, uploader

# === /start command ===
async def start(update: Update, context):
    await update.message.reply_text(
        "👋 Welcome! Send me a YouTube, Instagram, Facebook, or Twitter link. I’ll download and send you the best quality video!"
    )

# === Handle any message ===
async def handle_message(update: Update, context):
    url = update.message.text.strip()
    chat = update.effective_chat
    user = update.effective_user

    await context.bot.send_chat_action(chat_id=chat.id, action="upload_document")

    file_path = None
    try:
        file_path, title, description, uploader = download_video(url)
        caption_text = build_caption(uploader, title, description, url)

        # Delete original message
        await context.bot.delete_message(chat_id=chat.id, message_id=update.message.message_id)

        try:
            await context.bot.send_video(
                chat_id=chat.id,
                video=open(file_path, 'rb'),
                caption=caption_text,
                parse_mode="MarkdownV2"
            )
        except:
            await context.bot.send_document(
                chat_id=chat.id,
                document=open(file_path, 'rb'),
                caption=caption_text[:1024],
                parse_mode="MarkdownV2"
            )

    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")
    finally:
        if file_path and os.path.exists(file_path):
            os.remove(file_path)  # Ensure cleanup even on errors

# === Main ===
def main():
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    keep_alive()
    application.run_polling()

if __name__ == "__main__":
    main()
