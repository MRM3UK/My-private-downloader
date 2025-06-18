from flask import Flask
from threading import Thread
from telegram import Update, InputFile
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
import os
import yt_dlp
import logging

# Telegram Bot Token and Log Channel
TOKEN = '8003189326:AAG7GiyBEGjGw6aBcKtUQp3kjZ0Rq5Mtxj8'
LOG_CHANNEL_ID = -1001002515325796

app = Flask(__name__)
@app.route('/')
def home():
    return "Bot is alive!"

def run():
    app.run(host="0.0.0.0", port=8080)

def keep_alive():
    Thread(target=run).start()

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

def download_media(url):
    filename = "video.mp4"
    ydl_opts = {
        'outtmpl': filename,
        'format': 'bestvideo+bestaudio/best',
        'merge_output_format': 'mp4',
        'quiet': True,
        'noplaylist': True,
        'nocheckcertificate': True,
    }
    if os.path.exists("cookies.txt"):
        ydl_opts['cookiefile'] = "cookies.txt"
    else:
        ydl_opts['cookiesfrombrowser'] = ('firefox',)

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
    return filename, info

def format_caption(info, url, username):
    uploader = info.get('uploader', 'Unknown')
    caption = info.get('description', '')
    short_caption = f"<spoiler>{caption[:4000]}</spoiler>" if caption else ""
    return f"Video by _{uploader}_
{short_caption}

{url}

@DownloaderReelbot"

def handle_message(update: Update, context: CallbackContext):
    url = update.message.text.strip()
    chat_id = update.effective_chat.id
    msg = update.message
    try:
        msg.reply_text("⏬ Downloading... please wait")
        file_path, info = download_media(url)
        caption = format_caption(info, url, msg.from_user.username)
        with open(file_path, 'rb') as video:
            context.bot.send_video(chat_id=chat_id, video=video, caption=caption, parse_mode='MarkdownV2')
            context.bot.send_video(chat_id=LOG_CHANNEL_ID, video=video, caption=f"📥 Downloaded by @{msg.from_user.username or msg.from_user.id}
From: {url}", parse_mode='Markdown')
        msg.delete()
        os.remove(file_path)
    except Exception as e:
        logging.error(e)
        msg.reply_text(f"❌ Error:\n{e}")

def start(update: Update, context: CallbackContext):
    update.message.reply_text(
        "🎬 *Welcome to Video Downloader Bot!*\n"
        "Thanks for using this bot! 🙏\n\n"
        "📥 *How to use:*\n"
        "• Send me any video link from:\n"
        "  ▪️ YouTube\n  ▪️ Instagram\n  ▪️ Facebook\n  ▪️ Twitter\n\n"
        "I'll download and send you the best quality video! 🚀\n\n"
        "Powered by @DownloaderReelbot",
        parse_mode='Markdown'
    )

def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
    updater.start_polling()
    keep_alive()
    updater.idle()

main()
