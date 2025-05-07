import requests
from bs4 import BeautifulSoup
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, ContextTypes
import asyncio
import ssl
import certifi
import os
from functools import partial

# Configuration
TELEGRAM_BOT_TOKEN = "8194226321:AAGyWFDAc0qobuOXt01CFM5lF0kxsLkIci4"
TELEGRAM_CHAT_ID = "YOUR_CHAT_ID"
TARGET_URL = "https://example.com"
VALUE_SELECTOR = "span#price"

# Global state
last_value = None

def fetch_current_value():
    """Fetch value from website with SSL verification disabled"""
    try:
        response = requests.get(TARGET_URL, verify=False, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        element = soup.select_one(VALUE_SELECTOR)
        return element.get_text().strip() if element else None
    except Exception as e:
        print(f"Fetch error: {e}")
        return None

async def send_alert(message):
    """Send message with proper SSL context"""
    ssl_context = ssl.create_default_context(cafile=certifi.where())
    bot = Bot(TELEGRAM_BOT_TOKEN)
    await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)

async def monitor(check_interval=60):
    """Monitor value changes"""
    global last_value
    while True:
        current = fetch_current_value()
        if current and current != last_value:
            if last_value is not None:
                await send_alert(f"🔔 Value Changed!\nOld: {last_value}\nNew: {current}")
            last_value = current
        await asyncio.sleep(check_interval)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    await update.message.reply_text("🤖 Monitoring Bot Active!\nUse /value to check current status")

async def get_value(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /value command"""
    current = fetch_current_value()
    reply = f"Current value: {current}" if current else "⚠️ Could not fetch value"
    await update.message.reply_text(reply)

def create_ssl_context():
    """Create SSL context with certifi certificates"""
    context = ssl.create_default_context()
    context.load_verify_locations(cafile=certifi.where())
    return context

async def post_init(application):
    """Start monitoring after initialization"""
    asyncio.create_task(monitor())

def main():
    """Configure and start the bot"""
    # Set environment variables for SSL
    os.environ['SSL_CERT_FILE'] = certifi.where()
    os.environ['REQUESTS_CA_BUNDLE'] = certifi.where()

    # Create application with default settings
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).post_init(post_init).build()

    # Add command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("value", get_value))

    print("🚀 Bot started and monitoring...")
    application.run_polling()

if __name__ == "__main__":
    main()