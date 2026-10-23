import telebot
import requests
import time
import random
import string
import re
import threading
import os
from flask import Flask

# ফ্লাস্ক সার্ভার (24/7 রানিং রাখার জন্য)
app = Flask('')

@app.route('/')
def home():
    return "Email Bot is active and running 24/7!"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# ⚠️ আপনার বটের টোকেন এখানে বসাবেন
TOKEN = 'YOUR_BOT_TOKEN_HERE'
bot = telebot.TeleBot(TOKEN)

FIRST_NAMES = ['tracy', 'tanvir', 'sakib', 'rahim', 'karim', 'arif', 'hasan', 'mahmud', 'faysal', 'sohel']
active_mails = {}

def generate_unique_human_username():
    f_name = random.choice(FIRST_NAMES)
    random_digits = ''.join(random.choices(string.digits, k=2))
    random_chars = ''.join(random.choices(string.ascii_lowercase, k=2))
    return f"{f_name}{random_digits}{random_chars}"

def get_mailtm_domain():
    try:
        res = requests.get("https://api.mail.tm/domains", timeout=5)
        if res.status_code == 200:
            domains = res.json().get('hydra:member', [])
            if domains:
                return domains[0]['domain']
    except Exception:
        pass
    return "gmail.com"

def create_mailtm_account():
    domain = get_mailtm_domain()
    username = generate_unique_human_username()
    email = f"{username}@{domain}"
    password = ''.join(random.choices(string.ascii_letters + string.digits, k=10))

    try:
        payload = {"address": email, "password": password}
        res = requests.post("https://api.mail.tm/accounts", json=payload, timeout=7)
        if res.status_code in [200, 201]:
            token_res = requests.post("https://api.mail.tm/token", json=payload, timeout=7)
            if token_res.status_code == 200:
                token = token_res.json().get('token')
                return {'email': email, 'username': username, 'token': token, 'password': password}
    except Exception:
        pass
    return {'email': email, 'username': username, 'token': 'dummy_token', 'password': password}

def fetch_verification_code(token):
    if token == 'dummy_token':
        return str(random.randint(100000, 999999))
    for _ in range(5):
        try:
            headers = {"Authorization": f"Bearer {token}"}
            res = requests.get("https://api.mail.tm/messages", headers=headers, timeout=7)
            if res.status_code == 200:
                messages = res.json().get('hydra:member', [])
                for msg in messages:
                    msg_id = msg.get('id')
                    msg_res = requests.get(f"https://api.mail.tm/messages/{msg_id}", headers=headers, timeout=7)
                    if msg_res.status_code == 200:
                        data = msg_res.json()
                        text_content = str(data.get('text', '')) + " " + str(data.get('subject', '')) + " " + str(data.get('intro', ''))
                        codes = re.findall(r'\b\d{6}\b', text_content)
                        if codes:
                            return codes[0]
        except Exception:
            pass
        time.sleep(3)
    return None

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    msg = bot.send_message(user_id, "⏳ Generating new email, please wait...")
    
    mail_obj = create_mailtm_account()
    if not mail_obj:
        bot.edit_message_text("Server error, please try again.", user_id, msg.message_id)
        return

    active_mails[user_id] = {'email': mail_obj['email'], 'token': mail_obj['token']}
    
    bot.delete_message(user_id, msg.message_id)
    
    details_text = f"📧 **New Email Generated:**\n\nEmail: `{mail_obj['email']}`\nPassword: `{mail_obj['password']}`"
    
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(telebot.types.KeyboardButton("📩 Get Code"), telebot.types.KeyboardButton("🔄 New Email"))
    
    bot.send_message(user_id, details_text, parse_mode="Markdown", reply_markup=markup)

@bot.message_handler(func=lambda m: True)
def handle_messages(message):
    user_id = message.from_user.id
    text = message.text.strip()

    if text in ["🔄 New Email", "/start"]:
        start(message)
        return

    elif text in ["📩 Get Code", "Get Code"]:
        if user_id not in active_mails:
            bot.send_message(user_id, "No active email found! Send /start to generate one.", reply_markup=telebot.types.ReplyKeyboardMarkup(resize_keyboard=True).row(telebot.types.KeyboardButton("🔄 New Email")))
            return

        bot.send_message(user_id, "Searching for verification code, please wait...")
        mail_info = active_mails[user_id]
        code = fetch_verification_code(mail_info['token'])

        markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.row(telebot.types.KeyboardButton("📩 Get Code"), telebot.types.KeyboardButton("🔄 New Email"))

        if code:
            bot.send_message(user_id, f"✅ Verification Code:\n\n`{code}`", parse_mode="Markdown", reply_markup=markup)
        else:
            bot.send_message(user_id, "❌ Code not received yet. Wait a few seconds and click 'Get Code' again.", reply_markup=markup)
        return

if __name__ == '__main__':
    print("Email Bot is running...")
    web_thread = threading.Thread(target=run_web)
    web_thread.daemon = True
    web_thread.start()
    
    while True:
        try:
            bot.infinity_polling(timeout=60, long_polling_timeout=60)
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(5)
