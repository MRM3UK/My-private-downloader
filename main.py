import os
import re
import logging
import yt_dlp
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from flask import Flask
from threading import Thread

# === CONFIG ===
TOKEN = "7658699792:AAGjX9RVnOncN7ZYaW-9F9Glu2nCkAioVSc"  # Replace with your bot token
DOWNLOAD_DIR = "downloads"
COOKIE_FILE = "cookies.txt"
BOT_USERNAME = "@Downloderprobdbot"  # Your bot username for credit

# Create downloads folder if not exists
os.makedirs(DOWNLOAD_DIR, exist_ok=True)
if not os.path.exists(COOKIE_FILE):
    open(COOKIE_FILE, 'a').close()  # create empty cookie file if missing

# Setup logging
logging.basicConfig(level=logging.INFO)

# Flask app for keep-alive
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is online!"

def run():
    port = int(os.getenv("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    Thread(target=run, daemon=True).start()

# Escape MarkdownV2 special chars for captions
def clean_caption(text):
    return re.sub(r'([_*`()~>#+=|{}.!\\-])', r'\\\1', text)

# Build caption with uploader, caption, url, and bot username
def build_caption(uploader, title, caption, url):
    caption_text = clean_caption(caption.strip() if caption else title)
    spoiler_caption = f"||{caption_text}||"
    final_caption = (
        f"Video by _{clean_caption(uploader)}_\n\n"
        f"{spoiler_caption}\n\n"
        f"{url}\n\n"
        f"{BOT_USERNAME}"
    )
    return final_caption[:1024]  # Telegram caption limit

# Download video using yt_dlp
def download_video(url):
    ydl_opts = {
        'format': 'bestvideo+bestaudio/best',
        'cookiefile': COOKIE_FILE,
        'outtmpl': f"{DOWNLOAD_DIR}/%(title).40s.%(ext)s",
        'quiet': True,
        'nocheckcertificate': True,
        'noplaylist': True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        title = info.get('title', '')
        desc = info.get('description', '') or info.get('caption', '')
        uploader = info.get('uploader', 'unknown')
        file_path = ydl.prepare_filename(info)
        return file_path, title, desc, uploader

# /start command handler
async def start(update: Update, context):
    await update.message.reply_text(
        "👋 Send me a YouTube, Instagram, Facebook, or Twitter video link and I'll download it for you!"
    )

# Handle incoming messages (video URLs)
async def handle_message(update: Update, context):
    url = update.message.text.strip()
    chat_id = update.effective_chat.id

    # Show 'uploading' action
    await context.bot.send_chat_action(chat_id=chat_id, action="upload_document")

    file_path = None
    try:
        file_path, title, description, uploader = download_video(url)
        caption = build_caption(uploader, title, description, url)

        # Delete original user message
        await context.bot.delete_message(chat_id=chat_id, message_id=update.message.message_id)

        # Try sending as video
        try:
            with open(file_path, 'rb') as video_file:
                await context.bot.send_video(
                    chat_id=chat_id,
                    video=video_file,
                    caption=caption,
                    parse_mode="MarkdownV2"
                )
        except Exception:
            # Fallback: send as document
            with open(file_path, 'rb') as doc_file:
                await context.bot.send_document(
                    chat_id=chat_id,
                    document=doc_file,
                    caption=caption[:1024],
                    parse_mode="MarkdownV2"
                )

    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")

    finally:
        # Cleanup downloaded file
        if file_path and os.path.exists(file_path):
            os.remove(file_path)

# Main function
def main():
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    keep_alive()
    application.run_polling()

if __name__ == "__main__":
    main()
