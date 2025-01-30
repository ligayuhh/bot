import telebot
import requests
import random
import string
import datetime
import uuid
import os

BOT_TOKEN = "8054788056:AAFnxZrzc-DqkpxV5DwAUrI1CjXQgJyOqP0"
API_KEY = "QcBRTV8Gy3pPAzg5SfrN"
BASE_URL = "https://alexraefra.com/api"
APPROVAL_LIST_URL = "https://raw.githubusercontent.com/RPW-ALEX1107GRAY/approvalSheet/main/approvalSheet.txt"

bot = telebot.TeleBot(BOT_TOKEN)

current_email = None
custom_email = None

# Generate or retrieve a unique key for each user
def get_user_key(user_id):
    key_file = f"/sdcard/.approval_key_{user_id}.txt"
    if os.path.exists(key_file):
        with open(key_file, "r") as file:
            return file.read().strip()
    else:
        new_key = uuid.uuid4().hex[:10].upper()
        with open(key_file, "w") as file:
            file.write(new_key)
        return new_key

# Check if the user's key is approved
def is_key_approved(user_key):
    try:
        response = requests.get(APPROVAL_LIST_URL)
        if response.status_code == 200:
            approved_keys = response.text.splitlines()
            return user_key in approved_keys
    except:
        pass
    return False

# Fetch available email domains
def get_domains():
    try:
        response = requests.get(f"{BASE_URL}/domains/{API_KEY}")
        response.raise_for_status()
        data = response.json()
        return data if isinstance(data, list) else data.get("domains", [])
    except requests.RequestException as e:
        print(f"Error fetching domains: {e}")
        return []

# Generate a random email
def generate_email():
    global current_email
    domains = get_domains()
    if not domains:
        return None
    random_domain = random.choice(domains)
    email = "".join(random.choices(string.ascii_letters + string.digits, k=10)) + "@" + random_domain
    try:
        requests.get(f"{BASE_URL}/email/{email}/{API_KEY}")
    except requests.RequestException as e:
        print(f"Error registering email: {e}")
        return None
    current_email = email
    return email

# Generate a custom email with a user-defined prefix
def generate_custom_email(custom_prefix):
    global custom_email
    domains = get_domains()
    if not domains:
        return None
    random_domain = random.choice(domains)
    email = f"{custom_prefix}@{random_domain}"
    try:
        requests.get(f"{BASE_URL}/email/{email}/{API_KEY}")
    except requests.RequestException as e:
        print(f"Error registering custom email: {e}")
        return None
    custom_email = email
    return email

# Format timestamps for better readability
def format_timestamp(timestamp):
    try:
        dt = datetime.datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
        return dt.strftime("%B %d, %Y %I:%M %p")
    except ValueError:
        return timestamp

# Fetch messages from inbox
def get_messages(email):
    try:
        response = requests.get(f"{BASE_URL}/messages/{email}/{API_KEY}")
        response.raise_for_status()
        data = response.json()
        return sorted(data, key=lambda x: x['timestamp']['date'], reverse=True) if isinstance(data, list) else []
    except requests.RequestException as e:
        print(f"Error fetching messages: {e}")
        return []

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    user_key = get_user_key(user_id)

    if is_key_approved(user_key):
        bot.reply_to(message, "✅ *Access Granted!* You can use all bot features.")
    else:
        bot.reply_to(message, f"❌ *Access Denied!*\n\n🔑 *Your Key:* `{user_key}`\n\nSend this key to @YourUsername for approval.")

@bot.message_handler(commands=['check_key'])
def check_key(message):
    user_id = message.from_user.id
    user_key = get_user_key(user_id)

    if is_key_approved(user_key):
        bot.reply_to(message, "✅ *Your key is approved.* You have access to this bot.")
    else:
        bot.reply_to(message, f"❌ *Your key is not approved yet.*\n\n🔑 *Your Key:* `{user_key}`\nSend this key to @YourUsername for approval.")

@bot.message_handler(commands=['genmail'])
def gen_email(message):
    email = generate_email()
    bot.reply_to(message, f"📧 *Your Random Email:* `{email}`" if email else "❌ Failed to generate an email. Try again later.")

@bot.message_handler(commands=['custom_email'])
def custom_email_handler(message):
    args = message.text.split(" ")
    if len(args) < 2:
        bot.reply_to(message, "⚠️ Please provide a custom prefix. Example: `/custom_email mycustomname`")
        return
    email = generate_custom_email(args[1])
    bot.reply_to(message, f"📧 *Your Custom Email:* `{email}`" if email else "❌ Failed to generate a custom email. Try again later.")

@bot.message_handler(commands=['genmail_inbox'])
def current_inbox(message):
    global current_email
    if not current_email:
        bot.reply_to(message, "📭 No current random email generated. Use `/genmail` to generate one.")
        return
    messages = get_messages(current_email)
    if messages:
        formatted_messages = [f"📌 *ID:* `{msg['id']}`\n✉️ *Subject:* {msg['subject']}\n👤 *From:* {msg['sender_name']} <{msg['sender_email']}>\n🕒 *Timestamp:* {format_timestamp(msg['timestamp']['date'])}" for msg in messages]
        bot.reply_to(message, f"📬 *Your Email:* `{current_email}`\n\n" + "\n\n".join(formatted_messages))
    else:
        bot.reply_to(message, f"📬 *Your Email:* `{current_email}`\n\n📭 No messages found in the inbox.")

@bot.message_handler(commands=['custom_inbox'])
def custom_inbox(message):
    global custom_email
    if not custom_email:
        bot.reply_to(message, "📭 No custom email generated. Use `/custom_email <prefix>` to create one.")
        return
    messages = get_messages(custom_email)
    if messages:
        formatted_messages = [f"📌 *ID:* `{msg['id']}`\n✉️ *Subject:* {msg['subject']}\n👤 *From:* {msg['sender_name']} <{msg['sender_email']}>\n🕒 *Timestamp:* {format_timestamp(msg['timestamp']['date'])}" for msg in messages]
        bot.reply_to(message, f"📬 *Your Email:* `{custom_email}`\n\n" + "\n\n".join(formatted_messages))
    else:
        bot.reply_to(message, f"📬 *Your Email:* `{custom_email}`\n\n📭 No messages found in the inbox.")

bot.set_my_commands([
    telebot.types.BotCommand("start", "Start the bot"),
    telebot.types.BotCommand("check_key", "Check if your key is approved"),
    telebot.types.BotCommand("genmail", "Generate a random email"),
    telebot.types.BotCommand("custom_email", "Generate a custom email with a prefix"),
    telebot.types.BotCommand("genmail_inbox", "View inbox for the current random email"),
    telebot.types.BotCommand("custom_inbox", "View inbox for the custom email"),
])

bot.infinity_polling()
