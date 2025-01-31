import telebot
import requests
import random
import string
import datetime

BOT_TOKEN = "8054788056:AAFnxZrzc-DqkpxV5DwAUrI1CjXQgJyOqP0"
API_KEY = "QcBRTV8Gy3pPAzg5SfrN"
BASE_URL = "https://alexraefra.com/api"

bot = telebot.TeleBot(BOT_TOKEN)
approved_users = {}  # Change to store user key and name
admin_id = 1292741412  # Replace with your Telegram ID

current_email = None
custom_email = None

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    if user_id not in approved_users:
        bot.reply_to(message, "❌ You are not approved yet. Please request approval using /my_key.")
        return
    bot.reply_to(message, "🤖 Welcome! You are approved. Use /genmail to generate an email.")

@bot.message_handler(commands=['genmail'])
def generate_random_email(message):
    user_id = message.from_user.id
    if user_id not in approved_users:
        bot.reply_to(message, "❌ You are not approved yet. Please request approval using /my_key.")
        return

    email = generate_email()
    if email:
        bot.reply_to(message, f"📧 Your generated email: {email}")
    else:
        bot.reply_to(message, "⚠️ Failed to generate email. Try again later.")

@bot.message_handler(commands=['genmail_inbox'])
def current_inbox(message):
    global current_email
    print(f"Current Email: {current_email}")  # Debugging line

    if not current_email:
        bot.reply_to(message, "No current random email generated. Use /genmail to generate one.")
        return
    
    messages = get_messages(current_email)
    print(f"Messages Retrieved: {messages}")  # Debugging line

    if messages:
        formatted_messages = [f"📌 ID: {msg['id']}\n✉️ Subject: {msg['subject']}\n👤 From: {msg['sender_name']} <{msg['sender_email']}>\n🕒 Timestamp: {format_timestamp(msg['timestamp']['date'])}" for idx, msg in enumerate(messages)]
        bot.reply_to(message, f"📬 Your Email: {current_email}\n\n" + "\n\n".join(formatted_messages))
    else:
        bot.reply_to(message, f"📬 Your Email: {current_email}\n\nNo messages found in the inbox.")

@bot.message_handler(commands=['custom_email'])
def generate_custom_email_handler(message):
    user_id = message.from_user.id
    if user_id not in approved_users:
        bot.reply_to(message, "❌ You are not approved yet. Please request approval using /my_key.")
        return

    try:
        custom_prefix = message.text.split()[1]
        email = generate_custom_email(custom_prefix)
        if email:
            bot.reply_to(message, f"📧 Your custom email: {email}")
        else:
            bot.reply_to(message, "⚠️ Failed to generate a custom email. Try again later.")
    except IndexError:
        bot.reply_to(message, "❌ Please provide a prefix. Example: /custom_email myname")

@bot.message_handler(commands=['custom_inbox'])
def check_custom_email_inbox(message):
    user_id = message.from_user.id
    if user_id not in approved_users:
        bot.reply_to(message, "❌ You are not approved yet. Please request approval using /my_key.")
        return

    global custom_email
    if not custom_email:
        bot.reply_to(message, "⚠️ You don't have a custom email. Generate one using /custom_email.")
        return

    messages = get_messages(custom_email)
    if messages:
        formatted_messages = [
            f"📌 ID: {msg['id']}\n✉️ Subject: {msg['subject']}\n👤 From: {msg['sender_name']} <{msg['sender_email']}>\n🕒 Timestamp: {format_timestamp(msg['timestamp']['date'])}"
            for msg in messages
        ]
        bot.reply_to(message, f"📬 Your Email: {custom_email}\n\n" + "\n\n".join(formatted_messages))
    else:
        bot.reply_to(message, "📭 No messages found in your inbox.")

@bot.message_handler(commands=['approved_list'])
def approved_list(message):
    if message.from_user.id == admin_id:
        if approved_users:
            approved_list = "\n".join([f"ID: {user_id}, Name: {user_info[1]}, Key: {user_info[0]}" for user_id, user_info in approved_users.items()])
            bot.reply_to(message, f"✅ Approved Users:\n{approved_list}")
        else:
            bot.reply_to(message, "❌ No users are currently approved.")
    else:
        bot.reply_to(message, "❌ You are not authorized to view the approved user list.")

def generate_user_key(user_id):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=10))

def get_domains():
    try:
        response = requests.get(f"{BASE_URL}/domains/{API_KEY}")
        response.raise_for_status()
        data = response.json()
        return data if isinstance(data, list) else data.get("domains", [])
    except requests.RequestException as e:
        print(f"Error fetching domains: {e}")
        return []

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

def format_timestamp(timestamp):
    try:
        dt = datetime.datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
        return dt.strftime("%B %d, %Y %I:%M %p")
    except ValueError:
        return timestamp

def get_messages(email):
    try:
        response = requests.get(f"{BASE_URL}/messages/{email}/{API_KEY}")
        response.raise_for_status()
        data = response.json()
        return sorted(data, key=lambda x: x['timestamp']['date'], reverse=True) if isinstance(data, list) else []
    except requests.RequestException as e:
        print(f"Error fetching messages: {e}")
        return []

@bot.message_handler(commands=['approve'])
def approve_user(message):
    if message.from_user.id == admin_id:
        try:
            user_id, user_name = map(str, message.text.split()[1:3])  # Expect user ID and user name
            user_id = int(user_id)
            user_key = generate_user_key(user_id)
            approved_users[user_id] = (user_key, user_name)  # Store user key and name
            bot.reply_to(message, f"✅ User {user_id} ({user_name}) has been approved with key: {user_key}")
        except (IndexError, ValueError):
            bot.reply_to(message, "❌ Please provide a valid user ID and name.")
    else:
        bot.reply_to(message, "❌ You are not authorized to approve users.")

@bot.message_handler(commands=['revoke'])
def revoke_user(message):
    if message.from_user.id == admin_id:
        try:
            user_id = int(message.text.split()[1])
            approved_users.pop(user_id, None)
            bot.reply_to(message, f"❌ User {user_id} has been revoked.")
        except (IndexError, ValueError):
            bot.reply_to(message, "❌ Please provide a valid user ID.")
    else:
        bot.reply_to(message, "❌ You are not authorized to revoke users.")

@bot.message_handler(commands=['my_key'])
def get_user_key(message):
    user_id = message.from_user.id

    if user_id in approved_users:
        bot.reply_to(message, f"✅ You are already approved!\n🔑 Your Key: `{user_id}`")
    else:
        bot.reply_to(message, f"🔑 Your Key: `{user_id}`\n\n⚠️ You are not approved yet. Send this ID to an admin for approval.")

@bot.message_handler(commands=['check_key'])
def check_key(message):
    if message.from_user.id in approved_users:
        bot.reply_to(message, "✅ Your key is approved.")
    else:
        bot.reply_to(message, "❌ Your key is not approved.")

bot.set_my_commands([
    telebot.types.BotCommand("start", "Start the bot"),
    telebot.types.BotCommand("genmail", "Generate a random email"),
    telebot.types.BotCommand("genmail_inbox", "Check inbox for current email"),
    telebot.types.BotCommand("custom_email", "Generate a custom email"),
    telebot.types.BotCommand("custom_inbox", "Check inbox for custom email"),
    telebot.types.BotCommand("approved_list", "View list of approved users (Admin only)"),
    telebot.types.BotCommand("my_key", "Get your key"),
    telebot.types.BotCommand("check_key", "Check if your key is approved"),
    telebot.types.BotCommand("approve", "Approve a user (Admin only)"),
    telebot.types.BotCommand("revoke", "Revoke a user's approval (Admin only)")
])

bot.polling()
