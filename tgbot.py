import telebot
import requests
import random
import string
import datetime
import uuid
import os
import threading
import time
import urllib3
import urllib
from urllib.request import urlopen

# Bot & API Configuration
BOT_TOKEN = "8054788056:AAFnxZrzc-DqkpxV5DwAUrI1CjXQgJyOqP0"
API_KEY = "QcBRTV8Gy3pPAzg5SfrN"
BASE_URL = "https://alexraefra.com/api"
APPROVAL_LIST_URL = "https://github.com/RPW-ALEX1107GRAY/approvalSheet/blob/main/approvalSheet.txt"

bot = telebot.TeleBot(BOT_TOKEN)

# Ensure the keys directory exists
KEYS_DIR = "./keys"
os.makedirs(KEYS_DIR, exist_ok=True)

# Cached approved keys (auto-refreshes every 30s)
approved_keys_cache = set()

def update_approved_keys():
    """ Fetch approved keys from the raw GitHub file and update the cache. """
    global approved_keys_cache
    while True:
        try:
            response = urlopen(APPROVAL_LIST_URL)
            approved_keys_cache = set(response.read().decode("utf-8").strip().split("\n"))
        except Exception as e:
            print(f"Error updating approval list: {e}")
        time.sleep(30)  # Refresh every 30 seconds

# Start background thread for approval updates
threading.Thread(target=update_approved_keys, daemon=True).start()

def get_user_key(user_id):
    """ Generate or retrieve a unique key for each user. """
    key_file = f"{KEYS_DIR}/approval_key_{user_id}.txt"

    if os.path.exists(key_file):
        with open(key_file, "r") as file:
            return file.read().strip()
    else:
        new_key = uuid.uuid4().hex[:10].upper()
        with open(key_file, "w") as file:
            file.write(new_key)
        return new_key

def is_key_approved(user_key):
    """ Check if the user's key is approved (cached for faster checks). """
    return user_key.strip() in approved_keys_cache

def restricted_access(func):
    """ Middleware to restrict bot access if key is not approved. """
    def wrapper(message):
        user_id = message.from_user.id
        user_key = get_user_key(user_id)

        if not is_key_approved(user_key):
            bot.reply_to(message, f"❌ Access Denied!\n\n🔑 Your Key: `{user_key}`\nSend this key to Alexander Grayson for approval.")
            return
        return func(message)
    return wrapper

def get_domains():
    """ Fetch available email domains from the API. """
    try:
        response = requests.get(f"{BASE_URL}/domains/{API_KEY}")
        response.raise_for_status()
        data = response.json()
        return data if isinstance(data, list) else data.get("domains", [])
    except requests.RequestException:
        return []

def generate_email():
    """ Generate a random email address from available domains. """
    domains = get_domains()
    if not domains:
        return None
    email = "".join(random.choices(string.ascii_letters + string.digits, k=10)) + "@" + random.choice(domains)
    try:
        requests.get(f"{BASE_URL}/email/{email}/{API_KEY}")
    except requests.RequestException:
        return None
    return email

def generate_custom_email(custom_prefix):
    """ Generate a custom email with a user-defined prefix. """
    domains = get_domains()
    if not domains:
        return None
    email = f"{custom_prefix}@{random.choice(domains)}"
    try:
        requests.get(f"{BASE_URL}/email/{email}/{API_KEY}")
    except requests.RequestException:
        return None
    return email

def get_messages(email):
    """ Fetch messages from the inbox of a given email. """
    try:
        response = requests.get(f"{BASE_URL}/messages/{email}/{API_KEY}")
        response.raise_for_status()
        data = response.json()
        return sorted(data, key=lambda x: x['timestamp']['date'], reverse=True) if isinstance(data, list) else []
    except requests.RequestException:
        return []

@bot.message_handler(commands=['start'])
def start(message):
    """ Handle /start command to check if user has access. """
    user_id = message.from_user.id
    user_key = get_user_key(user_id)

    if is_key_approved(user_key):
        bot.reply_to(message, "✅ Access Granted! You can use all bot features.")
    else:
        bot.reply_to(message, f"❌ Access Denied!\n\n🔑 Your Key: `{user_key}`\nSend this key to Alexander Grayson for approval.")

@bot.message_handler(commands=['check_key'])
def check_key(message):
    """ Handle /check_key command to check approval status. """
    user_id = message.from_user.id
    user_key = get_user_key(user_id)

    if is_key_approved(user_key):
        bot.reply_to(message, "✅ Your key is approved. You have access to this bot.")
    else:
        bot.reply_to(message, f"❌ Your key is not approved yet.\n\n🔑 Your Key: `{user_key}`\nSend this key to Alexander Grayson for approval.")

@bot.message_handler(commands=['genmail'])
@restricted_access
def gen_email(message):
    """ Generate a random email and send it to the user. """
    email = generate_email()
    bot.reply_to(message, f"📧 Your Random Email: `{email}`" if email else "❌ Failed to generate an email. Try again later.")

@bot.message_handler(commands=['custom_email'])
@restricted_access
def custom_email_handler(message):
    """ Generate a custom email with a user-defined prefix. """
    args = message.text.split(" ")
    if len(args) < 2:
        bot.reply_to(message, "⚠️ Please provide a custom prefix. Example: `/custom_email mycustomname`")
        return
    email = generate_custom_email(args[1])
    bot.reply_to(message, f"📧 Your Custom Email: `{email}`" if email else "❌ Failed to generate a custom email. Try again later.")

@bot.message_handler(commands=['genmail_inbox'])
@restricted_access
def current_inbox(message):
    """ Retrieve inbox for the most recently generated random email. """
    email = generate_email()
    if not email:
        bot.reply_to(message, "📭 No current random email generated. Use `/genmail` to generate one.")
        return
    messages = get_messages(email)
    if messages:
        formatted_messages = [f"📌 ID: `{msg['id']}`\n✉️ Subject: {msg['subject']}\n👤 From: {msg['sender_name']} <{msg['sender_email']}>\n🕒 Time: {msg['timestamp']['date']}" for msg in messages]
        bot.reply_to(message, f"📬 Your Email: `{email}`\n\n" + "\n\n".join(formatted_messages))
    else:
        bot.reply_to(message, f"📬 Your Email: `{email}`\n\n📭 No messages found.")

bot.set_my_commands([
    telebot.types.BotCommand("start", "Start the bot"),
    telebot.types.BotCommand("check_key", "Check if your key is approved"),
    telebot.types.BotCommand("genmail", "Generate a random email"),
    telebot.types.BotCommand("custom_email", "Generate a custom email with a prefix"),
    telebot.types.BotCommand("genmail_inbox", "View inbox for the current random email")
])

bot.infinity_polling()
