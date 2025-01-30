import telebot
import requests
import random
import string
import re

BOT_TOKEN = "8054788056:AAFnxZrzc-DqkpxV5DwAUrI1CjXQgJyOqP0"
API_KEY = "QcBRTV8Gy3pPAzg5SfrN"
BASE_URL = "https://alexraefra.com/api"

bot = telebot.TeleBot(BOT_TOKEN)

current_email = None
custom_email = None

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

def get_messages(email):
    try:
        response = requests.get(f"{BASE_URL}/messages/{email}/{API_KEY}")
        response.raise_for_status()
        data = response.json()
        return data if isinstance(data, list) else []
    except requests.RequestException as e:
        print(f"Error fetching messages: {e}")
        return []

def clean_html(raw_html):
    raw_html = re.sub(r'<style.*?>.*?</style>', '', raw_html, flags=re.DOTALL)  # Remove CSS
    raw_html = re.sub(r'<br\s*/?>', '\n', raw_html)  # Replace <br> with newline
    raw_html = re.sub(r'</p>|</div>|</li>', '\n', raw_html)  # Preserve spacing for block elements
    raw_html = re.sub(r'<.*?>', '', raw_html)  # Remove all other HTML tags
    raw_html = re.sub(r'&nbsp;', ' ', raw_html)  # Replace non-breaking space with normal space
    raw_html = re.sub(r'\s+', ' ', raw_html)  # Normalize multiple spaces
    return raw_html.strip()

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "Welcome! Use the menu below to explore commands.")

@bot.message_handler(commands=['genmail'])
def gen_email(message):
    email = generate_email()
    bot.reply_to(message, f"Your Random Email: {email}" if email else "Failed to generate an email. Try again later.")

@bot.message_handler(commands=['custom_email'])
def custom_email_handler(message):
    args = message.text.split(" ")
    if len(args) < 2:
        bot.reply_to(message, "Please provide a custom prefix. Example: /custom_email mycustomname")
        return
    email = generate_custom_email(args[1])
    bot.reply_to(message, f"Your Custom Email: {email}" if email else "Failed to generate a custom email. Try again later.")

@bot.message_handler(commands=['genmail_inbox'])
def current_inbox(message):
    global current_email
    if not current_email:
        bot.reply_to(message, "No current random email generated. Use /genmail to generate one.")
        return
    messages = get_messages(current_email)
    if messages:
        formatted_messages = [
            f"ID: {msg['id']}\nSubject: {msg['subject']}\nFrom: {msg['sender_name']} <{msg['sender_email']}>\nTimestamp: {msg['timestamp']['date']}\nContent: {clean_html(msg['content'])}"
            for msg in messages
        ]
        bot.reply_to(message, "\n\n".join(formatted_messages))
    else:
        bot.reply_to(message, "No messages found in the current random email inbox.")

@bot.message_handler(commands=['custom_inbox'])
def custom_inbox(message):
    global custom_email
    if not custom_email:
        bot.reply_to(message, "No custom email generated. Use /custom_email <prefix> to create one.")
        return
    messages = get_messages(custom_email)
    if messages:
        formatted_messages = [
            f"ID: {msg['id']}\nSubject: {msg['subject']}\nFrom: {msg['sender_name']} <{msg['sender_email']}>\nTimestamp: {msg['timestamp']['date']}\nMessage: {clean_html(msg['content'])}"
            for msg in messages
        ]
        bot.reply_to(message, "\n\n".join(formatted_messages))
    else:
        bot.reply_to(message, "No messages found in the custom email inbox.")

bot.set_my_commands([
    telebot.types.BotCommand("start", "Start the bot"),
    telebot.types.BotCommand("genmail", "Generate a random email"),
    telebot.types.BotCommand("custom_email", "Generate a custom email with a prefix"),
    telebot.types.BotCommand("genmail_inbox", "View inbox for the current random email"),
    telebot.types.BotCommand("custom_inbox", "View inbox for the custom email"),
])

bot.infinity_polling()
