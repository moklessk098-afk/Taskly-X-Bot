import telebot
import requests
import time
import random
import string
import threading
import re
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

# Bot Configuration
TOKEN = '8884874905:AAFtdp9FTiCnFKw0MN6mN0Q2Yd7Jw6FAJLY'
CHANNEL_USERNAME = '@taandob7'
ADMIN_ID = 8702921423  # আপনার এডমিন আইডি
bot = telebot.TeleBot(TOKEN)

# Mail.tm API Base URL
BASE_URL = 'https://api.mail.tm'

# In-memory Database
users = {}  
active_mails = {}  
blocked_users = set()

def get_session():
    session = requests.Session()
    adapter = requests.adapters.HTTPAdapter(max_retries=3)
    session.mount('https://', adapter)
    return session

session = get_session()

def is_subscribed(user_id):
    try:
        member = bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ['creator', 'administrator', 'member']
    except Exception:
        return False

# সাধারণ ইউজারের জন্য কিবোর্ড
def main_keyboard(user_id):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(KeyboardButton("📧 Gen Mail"), KeyboardButton("📩 Check OTP"))
    markup.row(KeyboardButton("💰 Balance"), KeyboardButton("👥 Referral"))
    markup.row(KeyboardButton("💳 Withdraw"))
    
    if user_id == ADMIN_ID:
        markup.row(KeyboardButton("🛡️ Admin Panel"))
        
    return markup

def check_join_keyboard():
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("📢 Join Channel", url=f"https://t.me/{CHANNEL_USERNAME.replace('@', '')}"))
    markup.add(InlineKeyboardButton("✅ Verify Subscription", callback_data="check_subscription"))
    return markup

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    if user_id in blocked_users:
        bot.send_message(user_id, "❌ আপনাকে এই বট থেকে ব্লক করা হয়েছে!")
        return

    args = message.text.split()
    
    if user_id not in users:
        users[user_id] = {'balance': 0.0, 'referrals': 0, 'referred_by': None}
        if len(args) > 1 and args[1].isdigit():
            referrer_id = int(args[1])
            if referrer_id != user_id and referrer_id in users:
                users[user_id]['referred_by'] = referrer_id
                users[referrer_id]['balance'] += 1000.0  # $1000 Referral Bonus
                users[referrer_id]['referrals'] += 1
                try:
                    bot.send_message(referrer_id, f"🎉 New Referral! You earned <b>$1000</b>!", parse_mode="HTML")
                except:
                    pass

    if not is_subscribed(user_id):
        bot.send_message(user_id, f"⚠️ You must join {CHANNEL_USERNAME} to use this bot!", reply_markup=check_join_keyboard())
        return

    bot.send_message(user_id, "✨ Welcome to Temp Mail Bot! Select an option below:", reply_markup=main_keyboard(user_id))

@bot.callback_query_handler(func=lambda call: call.data == "check_subscription")
def verify_sub(call):
    user_id = call.from_user.id
    if is_subscribed(user_id):
        bot.answer_callback_query(call.id, "✅ Verified!")
        bot.send_message(user_id, "✨ Welcome! Select an option below:", reply_markup=main_keyboard(user_id))
    else:
        bot.answer_callback_query(call.id, "❌ You haven't joined yet!", show_alert=True)

# ইনলাইন ব্লক/আনব্লক বাটন হ্যান্ডলার
@bot.callback_query_handler(func=lambda call: call.data.startswith(("block_", "unblock_")))
def handle_block_callback(call):
    if call.from_user.id != ADMIN_ID:
        return
    
    action, target_id_str = call.data.split("_")
    target_id = int(target_id_str)
    
    if action == "block":
        blocked_users.add(target_id)
        bot.answer_callback_query(call.id, f"✅ User {target_id} Blocked!")
        bot.send_message(call.message.chat.id, f"🚫 <b>User <code>{target_id}</code> has been blocked!</b>", parse_mode="HTML")
    elif action == "unblock":
        if target_id in blocked_users:
            blocked_users.remove(target_id)
        bot.answer_callback_query(call.id, f"✅ User {target_id} Unblocked!")
        bot.send_message(call.message.chat.id, f"✅ <b>User <code>{target_id}</code> has been unblocked!</b>", parse_mode="HTML")

@bot.message_handler(func=lambda m: m.text == "🛡️ Admin Panel")
def admin_panel(message):
    user_id = message.from_user.id
    if user_id != ADMIN_ID:
        return
    
    admin_markup = ReplyKeyboardMarkup(resize_keyboard=True)
    admin_markup.row(KeyboardButton("👥 Total Users"), KeyboardButton("🔙 Main Menu"))
    bot.send_message(user_id, "🛡️ <b>Welcome to Admin Panel</b>\n\nChoose an option below or use commands:\n👉 <code>/block UID</code> - Block a user\n👉 <code>/unblock UID</code> - Unblock a user", reply_markup=admin_markup, parse_mode="HTML")

@bot.message_handler(func=lambda m: m.text == "🔙 Main Menu")
def main_menu(message):
    user_id = message.from_user.id
    bot.send_message(user_id, "🏠 Returned to Main Menu:", reply_markup=main_keyboard(user_id))

@bot.message_handler(func=lambda m: m.text == "👥 Total Users")
def admin_total_users(message):
    user_id = message.from_user.id
    if user_id != ADMIN_ID:
        return
    
    if not users:
        bot.send_message(user_id, "📭 বটে এখনো কোনো ইউজার নেই!")
        return
    
    total_users = len(users)
    bot.send_message(user_id, f"👥 <b>Total Users: {total_users}</b>", parse_mode="HTML")
    
    for uid, data in users.items():
        try:
            chat_info = bot.get_chat(uid)
            name = chat_info.first_name if chat_info.first_name else "No Name"
            username = f"@{chat_info.username}" if chat_info.username else "No Username"
        except:
            name = "Unknown"
            username = "N/A"
            
        balance = data.get('balance', 0.0)
        status = "🔴 Blocked" if uid in blocked_users else "🟢 Active"
        
        info_text = f"👤 <b>Name:</b> {name}\n🆔 <b>UID:</b> <code>{uid}</code>\n🔗 <b>Username:</b> {username}\n💰 <b>Balance:</b> ${balance:.2f}\n📌 <b>Status:</b> {status}"
        
        markup = InlineKeyboardMarkup()
        if uid != ADMIN_ID:
            if uid in blocked_users:
                markup.add(InlineKeyboardButton("✅ Unblock User", callback_data=f"unblock_{uid}"))
            else:
                markup.add(InlineKeyboardButton("🚫 Block User", callback_data=f"block_{uid}"))
        
        bot.send_message(user_id, info_text, reply_markup=markup, parse_mode="HTML")

@bot.message_handler(commands=['block'])
def block_user_cmd(message):
    if message.from_user.id != ADMIN_ID:
        return
    args = message.text.split()
    if len(args) > 1 and args[1].isdigit():
        target_id = int(args[1])
        blocked_users.add(target_id)
        bot.send_message(message.chat.id, f"✅ ইউজার আইডি <code>{target_id}</code> সফলভাবে ব্লক করা হয়েছে।", parse_mode="HTML")
    else:
        bot.send_message(message.chat.id, "⚠️ সঠিক নিয়মে লিখুন। যেমন: <code>/block 123456789</code>", parse_mode="HTML")

@bot.message_handler(commands=['unblock'])
def unblock_user_cmd(message):
    if message.from_user.id != ADMIN_ID:
        return
    args = message.text.split()
    if len(args) > 1 and args[1].isdigit():
        target_id = int(args[1])
        if target_id in blocked_users:
            blocked_users.remove(target_id)
            bot.send_message(message.chat.id, f"✅ ইউজার আইডি <code>{target_id}</code> আনব্লক করা হয়েছে।", parse_mode="HTML")
        else:
            bot.send_message(message.chat.id, "⚠️ এই ইউজারটি ব্লক লিস্টে নেই।")

@bot.message_handler(commands=['users'])
def users_cmd(message):
    admin_total_users(message)

@bot.message_handler(func=lambda m: m.text == "📧 Gen Mail")
def gen_mail(message):
    user_id = message.from_user.id
    if user_id in blocked_users:
        bot.send_message(user_id, "❌ আপনাকে এই বট থেকে ব্লক করা হয়েছে!")
        return
    if user_id not in users:
        users[user_id] = {'balance': 0.0, 'referrals': 0, 'referred_by': None}

    if not is_subscribed(user_id):
        bot.send_message(user_id, f"⚠️ Please join {CHANNEL_USERNAME} first!", reply_markup=check_join_keyboard())
        return

    msg = bot.send_message(user_id, "🔄 Generating email...")
    try:
        dom_res = session.get(f"{BASE_URL}/domains", timeout=10)
        if dom_res.status_code != 200:
            bot.edit_message_text("⚠️ Server busy, try again.", user_id, msg.message_id)
            return
            
        domains = dom_res.json().get('hydra:member', [])
        if not domains:
            bot.edit_message_text("❌ Domain service unavailable!", user_id, msg.message_id)
            return
        
        domain = domains[0]['domain']
        username = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
        email = f"{username}@{domain}"
        password = "Password123!"

        res = session.post(f"{BASE_URL}/accounts", json={"address": email, "password": password}, timeout=10)
        if res.status_code == 201:
            token_res = session.post(f"{BASE_URL}/token", json={"address": email, "password": password}, timeout=10)
            if token_res.status_code != 200:
                bot.edit_message_text("⚠️ Server busy, try again.", user_id, msg.message_id)
                return
                
            token = token_res.json()['token']

            active_mails[user_id] = {'email': email, 'token': token, 'last_msg_id': None}
            
            funny_email_quotes = [
                "কি রাগ করলা? নাও টাটকা ইমেইল নাও!",
                "হা হা, এই নাও তোমার কাঙ্ক্ষিত ইমেইল!",
                "রাগ করো কেন বস, এই নাও ফ্রেশ মেইল!",
                "এবারে কাজ হবে তো? এই নাও ইমেইল!"
            ]
            selected_email_line = random.choice(funny_email_quotes)
            
            bot.edit_message_text(f"✅ <b>Your Temp Email:</b>\n\n<code>{email}</code>\n\n💬 <i>{selected_email_line}</i>", user_id, msg.message_id, parse_mode="HTML")
            
            threading.Thread(target=auto_check_otp, args=(user_id, token), daemon=True).start()
        else:
            bot.edit_message_text("⚠️ Server busy, try again.", user_id, msg.message_id)
    except Exception as e:
        bot.edit_message_text("⚠️ Server busy, try again.", user_id, msg.message_id)

def auto_check_otp(user_id, token):
    funny_quotes = [
        "🏃‍♂️ লুঙ্গি পরে দৌড়াও, কোড চলে এসেছে!",
        "🔥 বস, কাঙ্ক্ষিত মাল (OTP) হাজির!",
        "⚡ বিদ্যুৎ গতিতে কোড চলে এল, জলদি কপি করো!",
        "😎 চোর পুলিশ খেলা শেষ, এই নাও তোমার কোড!"
    ]
    
    headers = {"Authorization": f"Bearer {token}"}
    for _ in range(600):
        if active_mails.get(user_id, {}).get('token') != token:
            break
        try:
            res = session.get(f"{BASE_URL}/messages", headers=headers, timeout=5)
            if res.status_code == 200:
                messages = res.json().get('hydra:member', [])
                if messages:
                    msg_id = messages[0]['id']
                    if active_mails.get(user_id, {}).get('last_msg_id') != msg_id:
                        active_mails[user_id]['last_msg_id'] = msg_id
                        msg_detail = session.get(f"{BASE_URL}/messages/{msg_id}", headers=headers, timeout=5).json()
                        body = msg_detail.get('text', '') or msg_detail.get('intro', '')
                        
                        codes = re.findall(r'\b\d{4,6}\b', body)
                        otp_code = codes[0] if codes else "Not found"
                        selected_funny_line = random.choice(funny_quotes)

                        if user_id not in users:
                            users[user_id] = {'balance': 0.0, 'referrals': 0, 'referred_by': None}
                        
                        users[user_id]['balance'] += 100.0

                        referrer_id = users[user_id].get('referred_by')
                        if referrer_id and referrer_id in users:
                            commission = 100.0 * 0.99
                            users[referrer_id]['balance'] += commission
                            try:
                                bot.send_message(referrer_id, f"💸 <b>Referral Commission!</b>\n\nYour referral earned an OTP, you received <b>${commission:.2f}</b> (99%)!", parse_mode="HTML")
                            except:
                                pass

                        # ডাইরেক্ট ওয়ান-টাচ কপি কোড বক্স (এর ওপর টাচ করলেই সরাসরি ক্লিপবোর্ডে কপি হয়ে যাবে)
                        bot.send_message(
                            user_id, 
                            f"📩 <b>OTP Code Received!</b>\n\n<code>{otp_code}</code>\n\n💬 <i>{selected_funny_line}</i>\n\n🎁 You earned <b>$100</b>!", 
                            parse_mode="HTML"
                        )
                        break
        except:
            pass
        time.sleep(2)

@bot.message_handler(func=lambda m: m.text == "📩 Check OTP")
def check_otp(message):
    user_id = message.from_user.id
    if user_id in blocked_users:
        bot.send_message(user_id, "❌ আপনাকে এই বট থেকে ব্লক করা হয়েছে!")
        return
    if user_id not in users:
        users[user_id] = {'balance': 0.0, 'referrals': 0, 'referred_by': None}

    if user_id not in active_mails or 'token' not in active_mails[user_id]:
        bot.send_message(user_id, "⚠️ আগে একটি নতুন মেইল জেনারেট করুন (Gen Mail এ ক্লিক করুন)!")
        return
    
    mail_info = active_mails[user_id]
    headers = {"Authorization": f"Bearer {mail_info['token']}"}
    try:
        res = session.get(f"{BASE_URL}/messages", headers=headers, timeout=10)
        if res.status_code == 200:
            messages = res.json().get('hydra:member', [])
            if messages:
                msg_id = messages[0]['id']
                if mail_info.get('last_checked_msg_id') != msg_id:
                    active_mails[user_id]['last_checked_msg_id'] = msg_id
                    users[user_id]['balance'] += 100.0
                    
                    referrer_id = users[user_id].get('referred_by')
                    if referrer_id and referrer_id in users:
                        commission = 100.0 * 0.99
                        users[referrer_id]['balance'] += commission
                        try:
                            bot.send_message(referrer_id, f"💸 <b>Referral Commission!</b>\n\nYour referral checked an OTP, you received <b>${commission:.2f}</b> (99%)!", parse_mode="HTML")
                        except:
                            pass
                
                msg_detail = session.get(f"{BASE_URL}/messages/{msg_id}", headers=headers, timeout=10).json()
                body = msg_detail.get('text', '') or msg_detail.get('intro', '')
                codes = re.findall(r'\b\d{4,6}\b', body)
                otp_code = codes[0] if codes else "Not found"
                
                bot.send_message(
                    user_id, 
                    f"📩 <b>Latest OTP Code:</b>\n\n<code>{otp_code}</code>\n\n😎 মালের কোনো ভেজাল নাই, টাটকা কোড!\n\n🎁 You earned <b>$100</b>!", 
                    parse_mode="HTML"
                )
            else:
                empty_funny_lines = [
                    "যার বউ নেই তার কোড ও নাই! একটু অপেক্ষা করো বস।",
                    "মেইল বক্স একদম ফাঁকা, কোড আসার এখনো সময় হয়নি!",
                    "খালি হাত নিয়ে ঘরে ফেরা লাগবে না, আরেকটু ওয়েট করো!",
                    "কোড কি তোমার মামাবাড়ির আবদার নাকি? একটু পরে আবার চেক করো!"
                ]
                selected_empty_line = random.choice(empty_funny_lines)
                bot.send_message(user_id, f"⌛ {selected_empty_line}")
        else:
            bot.send_message(user_id, "⚠️ টোকেন ম্যাচ করছে না! দয়া করে নতুন করে আবার একটি <code>Gen Mail</code> নিন।", parse_mode="HTML")
    except:
        bot.send_message(user_id, "❌ Error checking mailbox.")

@bot.message_handler(func=lambda m: m.text == "💰 Balance")
def balance(message):
    user_id = message.from_user.id
    if user_id in blocked_users:
        bot.send_message(user_id, "❌ আপনাকে এই বট থেকে ব্লক করা হয়েছে!")
        return
    if user_id not in users:
        users[user_id] = {'balance': 0.0, 'referrals': 0, 'referred_by': None}
    
    user_data = users[user_id]
    bot.send_message(user_id, f"👤 <b>Your Account Info</b>\n\n💰 Balance: <b>${user_data['balance']:.2f}</b>\n👥 Total Referrals: <b>{user_data['referrals']}</b>", parse_mode="HTML")

@bot.message_handler(func=lambda m: m.text == "👥 Referral")
def referral(message):
    user_id = message.from_user.id
    if user_id in blocked_users:
        bot.send_message(user_id, "❌ আপনাকে এই বট থেকে ব্লক করা হয়েছে!")
        return
    bot_username = bot.get_me().username
    ref_link = f"https://t.me/{bot_username}?start={user_id}"
    bot.send_message(user_id, f"🔗 <b>Your Referral Link:</b>\n\n<code>{ref_link}</code>\n\n🎁 Earn <b>$1000</b> for each friend you invite & <b>99% lifetime commission</b> on their OTP earnings!", parse_mode="HTML")

@bot.message_handler(func=lambda m: m.text == "💳 Withdraw")
def withdraw(message):
    user_id = message.from_user.id
    if user_id in blocked_users:
        bot.send_message(user_id, "❌ আপনাকে এই বট থেকে ব্লক করা হয়েছে!")
        return
    if user_id not in users:
        users[user_id] = {'balance': 0.0, 'referrals': 0, 'referred_by': None}

    user_data = users[user_id]
    
    if user_data['balance'] < 5000:
        funny_low_balance_quotes = [
            f"⚠️ তোমার ব্যালেন্স আছে মাত্র <b>${user_data['balance']:.2f}</b>! ফকিরি হালাত থেকে বাঁচতে আগে ৫০০০ ডলার বানাও, তারপর টাকা তোলার স্বপ্ন দেখো!",
            f"💸 পকেটে আছে মোটে <b>${user_data['balance']:.2f}</b>, আর তুলতে চাও ৫০০০! এত বড়লোক হওয়ার শখ কেন বস? আগে ইনভাইট করো!",
            f"🚫 একাউন্টে ব্যালেন্স কই যে উইথড্র করবা? বর্তমান ব্যালেন্স: <b>${user_data['balance']:.2f}</b>। যাও, আগে কামাই করে এসো!",
            f"😅 এই গরিব অবস্থায় উইথড্র দিতে গেলে ব্যাংকও মাইর দিবো! ব্যালেন্স অন্তত <b>$5000</b> করো, আছে মাত্র <b>${user_data['balance']:.2f}</b>।"
        ]
        bot.send_message(user_id, random.choice(funny_low_balance_quotes), parse_mode="HTML")
    else:
        funny_success_quotes = [
            "🎉 বাহ্ বস! কোটিপতি হয়ে গেলা নাকি? তোমার উইথড্র রিকোয়েস্ট মহাশূন্যে পাঠিয়ে দেওয়া হয়েছে (টাকা জীবনেও পাবা না, জাস্ট মজা নিলাম)! 😎",
            "🚀 উইথড্র সাকসেসফুল! হেলিকপ্টার রেডি আছে, গিয়ে টাকা নিয়ে আসো (অবশ্যই খপচ বা কল্পনায়)! 😂",
            "🤑 বাম্পার অফার! তোমার উইথড্র রিকোয়েস্ট এডমিনের কাছে গেছে, এডমিন এখন থাইল্যান্ডে ঘাস খাচ্ছে ফিরে এসে দিবোনি!",
            "🎉 অভিনন্দন! তুমি সফলভাবে ফেক ডলার উইথড্র করে ফেলছ! পকেট চেক করে দেখো এক টাকাও নাই! 🤣"
        ]
        bot.send_message(user_id, random.choice(funny_success_quotes), parse_mode="HTML")

print("Bot is running...")
bot.infinity_polling()
