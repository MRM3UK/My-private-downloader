import os
import yt_dlp
from telegram import ChatAction, ParseMode
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from flask import Flask
from threading import Thread
import re

# === CONFIG ===
TOKEN = "8003189326:AAG7GiyBEGjGw6aBcKtUQp3kjZ0Rq5Mtxj8"  # Replace with your bot token
DOWNLOAD_DIR = "downloads"
COOKIE_FILE = "cookies.txt"
BOT_USERNAME = "@DownloaderReelbot"

os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# === Keep-alive with Flask (Replit) ===
app = Flask('')

@app.route('/')
def home():
    return "Bot is online!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    Thread(target=run).start()

# === Clean caption (escape Markdown) ===
def clean_caption(text):
    return re.sub(r'([_*`()~>#+=|{}.!\\-])', r'\\\1', text)

# === Format final caption ===
def build_caption(insta_username, title, caption, url):
    caption = clean_caption(caption.strip() if caption else title)
    spoiler_caption = f"||{caption}||"
    final_caption = (
        f" Video by _{insta_username}_\n\n"
        f"{spoiler_caption}\n\n"
        f"{url}\n\n"
        f"{BOT_USERNAME}"
    )
    return final_caption[:1024]

# === Download video ===
def download_video(url):
    ydl_opts = {
        'format': 'best',
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
def start(update, context):
    update.message.reply_text("👋 Welcome! Send me a YouTube, Instagram, Facebook, or Twitter link. I’ll download and send you the best quality video!")

# === Handle any message ===
def handle_message(update, context):
    url = update.message.text.strip()
    chat = update.effective_chat
    user = update.effective_user

    context.bot.send_chat_action(chat_id=chat.id, action=ChatAction.UPLOAD_DOCUMENT)

    try:
        file_path, title, description, uploader = download_video(url)
        caption_text = build_caption(uploader, title, description, url)

        # Delete original message
        context.bot.delete_message(chat_id=chat.id, message_id=update.message.message_id)

        try:
            context.bot.send_video(
                chat_id=chat.id,
                video=open(file_path, 'rb'),
                caption=caption_text,
                parse_mode=ParseMode.MARKDOWN
            )
        except:
            context.bot.send_document(
                chat_id=chat.id,
                document=open(file_path, 'rb'),
                caption=caption_text[:1024],
                parse_mode=ParseMode.MARKDOWN
            )

        os.remove(file_path)

    except Exception as e:
        update.message.reply_text(f"❌ Error: {str(e)}")

# === Main ===
def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

    updater.start_polling()
    keep_alive()
    updater.idle()

main()