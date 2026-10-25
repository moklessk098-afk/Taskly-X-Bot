import telebot
import requests
import time
import random
import string
import re
import datetime
import pyotp
import io
import openpyxl
import threading
import os
import math
import hashlib
from flask import Flask

app = Flask('')

@app.route('/')
def home():
    return "Bot is active and running 24/7!"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

TOKEN = '8666711380:AAGLnSP2rzflGpIb1gyPNcegOcXWF7yO_Xg'
CHANNEL_USERNAME = '@taandob7'
ADMIN_ID = 8702921423
BOT_USERNAME = 'TasklyX_BD_Bot'

bot = telebot.TeleBot(TOKEN, parse_mode=None)

SETTINGS = {
    'task1_name': 'Twitter_2fa_auth_token',
    'task2_name': 'Twitter_2FA_Only',
    'reward_tw_token': 0.03,    
    'reward_tw_2fa': 0.03,      
    'usd_to_bdt': 125.0,        
    'withdraw_fee_bdt': 5.0,    
    'min_withdraw_bdt': 5.0,   
    'withdraw_enabled': True,   
    'bkash_enabled': True,
    'nagad_enabled': True,
    'binance_enabled': True,
    'pwd_mode': 'random',       
    'pwd_target_task': 'BOTH',  
    'custom_pwd_value': 'TasklyABC', 
    'pwd_length': 10,           
    'auto_report_enabled': False, 
    'auto_report_task': 'ALL',
    'auto_report_interval': 30, 
    'auto_approve_pct': 80.0,
    'custom_check_reject_pct': 3.5,  
    'custom_check_reject_enabled': True,
    'admin_pin': '4875',        
    'top_enabled': True,
    'top_reset_mode': 'daily_10pm', 
    'top_reset_interval_mins': 1440,
    'top_reset_timestamp': time.time() + 86400,
    'last_top_reset_date': '',
    'top_rewards': {1: 1.00, 2: 0.50, 3: 0.30, 4: 0.20, 5: 0.10},
    'ref_enabled': True,
    'ref_commission_pct': 10.0,
    'tw_2fa_enabled': True,
    'tw_token_enabled': True,
    'task_report_timer_text': 'Every 30 minutes'
}

videos_list = [
    {
        'title': 'Twitter Account Creation Guide',
        'type': 'url',
        'content': 'https://t.me/'
    }
]

FIRST_NAMES = ['tracy', 'tanvir', 'sakib', 'rahim', 'karim', 'arif', 'hasan', 'mahmud', 'faysal', 'sohel', 'nayan', 'rakib', 'imran', 'fahim', 'joy', 'roni']

users = {}  
active_mails = {}  
user_steps = {}       
user_acc_data = {}   
submitted_accounts = []  
rejected_accounts_db = []
rejected_history_db = set()
used_emails_db = set()
used_codes_db = set()
withdraw_requests = []  
blocked_users = set()
lifetime_usernames = set() 
downloaded_status = {'task1': False, 'task2': False}

def get_user_data(user_id, name="User"):
    if user_id not in users:
        users[user_id] = {
            'name': name, 
            'balance': 0.0, 
            'total_earned': 0.0, 
            'completed_tasks': 0,
            'referral_count': 0,
            'ref_earned': 0.0,
            'referrals_list': []
        }
    return users[user_id]

def is_subscribed(user_id):
    try:
        member = bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ['creator', 'administrator', 'member']
    except Exception:
        return False

def main_keyboard(user_id):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(telebot.types.KeyboardButton("💰 Balance"), telebot.types.KeyboardButton("📋 Tasks"))
    markup.row(telebot.types.KeyboardButton("📤 Withdraw"), telebot.types.KeyboardButton("👤 Profile"))
    markup.row(telebot.types.KeyboardButton("🏆 Top Leaderboard"), telebot.types.KeyboardButton("👥 Referral"))
    markup.row(telebot.types.KeyboardButton("🎬 Video Tutorial"))
    if user_id == ADMIN_ID:
        markup.row(telebot.types.KeyboardButton("👑 Admin Panel"))
    return markup

def tasks_keyboard():
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    r_token = SETTINGS['reward_tw_token']
    r_2fa = SETTINGS['reward_tw_2fa']
    t1_name = SETTINGS['task1_name']
    t2_name = SETTINGS['task2_name']

    if SETTINGS.get('tw_token_enabled', True):
        markup.row(telebot.types.KeyboardButton(f"🐦 {t1_name} (${r_token:.4f})"))
    if SETTINGS.get('tw_2fa_enabled', True):
        markup.row(telebot.types.KeyboardButton(f"🔥 {t2_name} (${r_2fa:.4f})"))
    markup.row(telebot.types.KeyboardButton("❌ Cancel"))
    return markup

def admin_panel_keyboard():
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(telebot.types.KeyboardButton("📋 Pending Accounts"), telebot.types.KeyboardButton("📤 Withdraw Requests"))
    markup.row(telebot.types.KeyboardButton("🏆 Top Control"), telebot.types.KeyboardButton("🔍 Search UID/Username"))
    markup.row(telebot.types.KeyboardButton("⚡ Batch Approve / Percentage"), telebot.types.KeyboardButton("🛠️ Task Control"))
    markup.row(telebot.types.KeyboardButton("💰 Change Price"), telebot.types.KeyboardButton("✏️ Change Task Names"))
    markup.row(telebot.types.KeyboardButton("🔐 Password Management"), telebot.types.KeyboardButton("⚙️ Payment Methods"))
    markup.row(telebot.types.KeyboardButton("👥 Referral Management"), telebot.types.KeyboardButton("👥 User Management"))
    markup.row(telebot.types.KeyboardButton("📢 Broadcast Message"), telebot.types.KeyboardButton("🎬 Video Management"))
    markup.row(telebot.types.KeyboardButton("📊 Task 1 Excel"), telebot.types.KeyboardButton("📊 Task 2 Excel (2FA)"))
    markup.row(telebot.types.KeyboardButton("🔍 Check Accounts via Username"), telebot.types.KeyboardButton("📥 Custom Username Check"))
    markup.row(telebot.types.KeyboardButton("📊 Database Stats"))
    markup.row(telebot.types.KeyboardButton("🏠 Main Menu"))
    return markup

def database_stats_keyboard():
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(telebot.types.KeyboardButton("📁 Upload Lifetime Excel"), telebot.types.KeyboardButton("📈 View Stats"))
    markup.row(telebot.types.KeyboardButton("🔍 Filter New vs Old Excel"))
    markup.row(telebot.types.KeyboardButton("👑 Admin Panel"))
    return markup

def batch_panel_keyboard():
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    rej_st = "🟢 ON" if SETTINGS.get('custom_check_reject_enabled', True) else "🔴 OFF"
    markup.row(telebot.types.KeyboardButton("✅ Batch Approve Usernames"), telebot.types.KeyboardButton("❌ Batch Reject Usernames"))
    markup.row(telebot.types.KeyboardButton("📊 Percentage Auto Process"), telebot.types.KeyboardButton("📉 Percentage Reject Process"))
    markup.row(telebot.types.KeyboardButton(f"🔄 Toggle Reject Sys: {rej_st}"))
    markup.row(telebot.types.KeyboardButton("👑 Admin Panel"))
    return markup

def excel_task1_menu():
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(telebot.types.KeyboardButton("📊 Download Excel: Task 1"), telebot.types.KeyboardButton("🗑️ Delete Task 1 Accounts"))
    markup.row(telebot.types.KeyboardButton("👑 Admin Panel"))
    return markup

def excel_2fa_menu():
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(telebot.types.KeyboardButton("📊 Download Excel: 2FA"), telebot.types.KeyboardButton("🗑️ Delete 2FA Accounts"))
    markup.row(telebot.types.KeyboardButton("👑 Admin Panel"))
    return markup

def password_mgmt_keyboard():
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    mode = SETTINGS.get('pwd_mode', 'random')
    m_rand = "✅ Random" if mode == 'random' else "Random"
    m_rand_date = "✅ Random + Date" if mode == 'random_date' else "Random + Date"
    m_same = "✅ Custom / Same" if mode == 'same' else "Custom / Same"

    target = SETTINGS.get('pwd_target_task', 'BOTH')
    t_text = f"Target Task: {target}"

    markup.row(telebot.types.KeyboardButton(f"Mode: {m_rand}"), telebot.types.KeyboardButton(f"Mode: {m_rand_date}"))
    markup.row(telebot.types.KeyboardButton(f"Mode: {m_same}"), telebot.types.KeyboardButton("✍️ Set Custom Password"))
    markup.row(telebot.types.KeyboardButton(f"🔄 {t_text}"))
    markup.row(telebot.types.KeyboardButton("👑 Admin Panel"))
    return markup

def referral_mgmt_keyboard():
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    ref_st = "🟢 ON" if SETTINGS.get('ref_enabled', True) else "🔴 OFF"
    markup.row(telebot.types.KeyboardButton(f"Toggle Referral: {ref_st}"))
    markup.row(telebot.types.KeyboardButton("💰 Set Referral Commission %"))
    markup.row(telebot.types.KeyboardButton("👑 Admin Panel"))
    return markup

def top_control_keyboard():
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    st = "🟢 ON" if SETTINGS.get('top_enabled', True) else "🔴 OFF"
    mode = SETTINGS.get('top_reset_mode')
    if mode == 'daily_10pm':
        mode_text = "Daily 10:00 PM"
    elif mode == 'sunday_10pm':
        mode_text = "Sunday 10:00 PM"
    else:
        mode_text = f"Every {SETTINGS.get('top_reset_interval_mins', 1440)} mins"

    markup.row(telebot.types.KeyboardButton(f"Toggle Leaderboard: {st}"))
    markup.row(telebot.types.KeyboardButton(f"Reset Schedule: {mode_text}"))
    markup.row(telebot.types.KeyboardButton("⏱️ Set Reset Minutes"))
    markup.row(telebot.types.KeyboardButton("🎁 Distribute Rewards & Reset Now"))
    markup.row(telebot.types.KeyboardButton("💰 Edit Rank Rewards"))
    markup.row(telebot.types.KeyboardButton("👑 Admin Panel"))
    return markup

def task_control_keyboard():
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    t1 = "🟢 ON" if SETTINGS.get('tw_token_enabled', True) else "🔴 OFF"
    t2 = "🟢 ON" if SETTINGS.get('tw_2fa_enabled', True) else "🔴 OFF"
    markup.row(telebot.types.KeyboardButton(f"Toggle Task 1: {t1}"), telebot.types.KeyboardButton(f"Toggle Task 2: {t2}"))
    markup.row(telebot.types.KeyboardButton("⏱️ Set Report Timer Text"))
    markup.row(telebot.types.KeyboardButton("👑 Admin Panel"))
    return markup

def payment_toggle_keyboard():
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    wd_st = "🟢 ON" if SETTINGS['withdraw_enabled'] else "🔴 OFF"
    bk_st = "🟢 ON" if SETTINGS['bkash_enabled'] else "🔴 OFF"
    ng_st = "🟢 ON" if SETTINGS['nagad_enabled'] else "🔴 OFF"
    bn_st = "🟢 ON" if SETTINGS['binance_enabled'] else "🔴 OFF"

    markup.row(telebot.types.KeyboardButton(f"Withdraw Sys: {wd_st}"), telebot.types.KeyboardButton(f"Bkash: {bk_st}"))
    markup.row(telebot.types.KeyboardButton(f"Nagad: {ng_st}"), telebot.types.KeyboardButton(f"Binance: {bn_st}"))
    markup.row(telebot.types.KeyboardButton("⚙️ Set Minimum Withdraw Limit"))
    markup.row(telebot.types.KeyboardButton("👑 Admin Panel"))
    return markup

def video_mgmt_keyboard():
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(telebot.types.KeyboardButton("➕ Add Video File / Link"), telebot.types.KeyboardButton("🗑️ Remove All Videos"))
    markup.row(telebot.types.KeyboardButton("👑 Admin Panel"))
    return markup

def clear_user_chat_session(user_id, chat_messages_dict):
    if user_id in chat_messages_dict:
        for msg_id in chat_messages_dict[user_id]:
            try:
                bot.delete_message(user_id, msg_id)
            except Exception:
                pass
        chat_messages_dict[user_id] = []

def alter_string_slightly(text_str):
    s = str(text_str).strip()
    if not s or len(s) <= 2:
        return s + "x"
    
    val_list = list(s)
    
    # প্রথম এবং শেষ অক্ষর বাদ দিয়ে শুধুমাত্র মাঝের অক্ষরগুলোর মধ্য থেকে ১টি অক্ষর পরিবর্তন করা
    middle_indices = list(range(1, len(val_list) - 1))
    
    hash_val = int(hashlib.md5(s.encode('utf-8')).hexdigest(), 16)
    idx = middle_indices[hash_val % len(middle_indices)]
    
    current_char = val_list[idx]
    
    # ছোট হাতের বর্ণ, বড় হাতের বর্ণ বা ডিজিটের মধ্যে ১টি নতুন ক্যারেক্টার বেছে নেওয়া
    if current_char.isdigit():
        allowed = [c for c in string.digits if c != current_char]
    elif current_char.isupper():
        allowed = [c for c in string.ascii_uppercase if c != current_char]
    else:
        allowed = [c for c in string.ascii_lowercase if c != current_char]
        
    if not allowed:
        allowed = [c for c in string.ascii_letters + string.digits if c != current_char]
        
    new_char = allowed[hash_val % len(allowed)]
    val_list[idx] = new_char
    
    return "".join(val_list)

def generate_unique_human_username():
    f_name = random.choice(FIRST_NAMES)
    random_digits = ''.join(random.choices(string.digits, k=2))
    random_chars = ''.join(random.choices(string.ascii_lowercase, k=2))
    return f"{f_name}{random_digits}{random_chars}"

def generate_password(task_name=None):
    target = SETTINGS.get('pwd_target_task', 'BOTH')
    if target != 'BOTH' and task_name:
        if target == 'task1' and task_name != SETTINGS['task1_name']:
            return ''.join(random.choices(string.ascii_letters + string.digits, k=10))
        if target == 'task2' and task_name != SETTINGS['task2_name']:
            return ''.join(random.choices(string.ascii_letters + string.digits, k=10))

    length = SETTINGS.get('pwd_length', 10)
    mode = SETTINGS.get('pwd_mode', 'random')
    chars = string.ascii_letters + string.digits
    
    if mode == 'same':
        return SETTINGS.get('custom_pwd_value', 'TasklyABC')
    elif mode == 'random_date':
        letters_part = ''.join(random.choices(string.ascii_letters, k=max(4, length - 2)))
        date_part = datetime.datetime.now().strftime("%d")
        return f"{letters_part}{date_part}"
    else: 
        return ''.join(random.choices(chars, k=length))

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

def create_mailtm_account(task_name=None):
    for _ in range(5):
        domain = get_mailtm_domain()
        username = generate_unique_human_username()
        email = f"{username}@{domain}"
        if email.lower() not in used_emails_db:
            password = generate_password(task_name)
            try:
                payload = {"address": email, "password": password}
                res = requests.post("https://api.mail.tm/accounts", json=payload, timeout=7)
                if res.status_code in [200, 201]:
                    token_res = requests.post("https://api.mail.tm/token", json=payload, timeout=7)
                    if token_res.status_code == 200:
                        token = token_res.json().get('token')
                        used_emails_db.add(email.lower())
                        return {'email': email, 'username': username, 'token': token, 'type': 'mailtm', 'password': password}
            except Exception:
                pass
    return None

def fetch_twitter_code(token):
    if token == 'dummy_token':
        return str(random.randint(100000, 999999))
    for _ in range(5):
        try:
            headers = {"Authorization": f"Bearer {token}"}
            res = requests.get("https://api.mail.tm/messages", headers=headers, timeout=7)
            if res.status_code == 200:
                messages = res.json().get('hydra:member', [])
                for msg in messages:
                    sender = str(msg.get('from', {}).get('address', '')).lower()
                    subject = str(msg.get('subject', '')).lower()
                    
                    if 'twitter' in sender or 'x.com' in sender or 'twitter' in subject or 'verification' in subject or 'confirm' in subject:
                        msg_id = msg.get('id')
                        msg_res = requests.get(f"https://api.mail.tm/messages/{msg_id}", headers=headers, timeout=7)
                        if msg_res.status_code == 200:
                            data = msg_res.json()
                            text_content = str(data.get('text', '')) + " " + str(data.get('subject', '')) + " " + str(data.get('intro', ''))
                            codes = re.findall(r'\b\d{6}\b', text_content)
                            if codes:
                                code = codes[0]
                                if code not in used_codes_db:
                                    used_codes_db.add(code)
                                    return code
        except Exception:
            pass
        time.sleep(3)
    return None

def extract_username(text):
    text = text.strip()
    match = re.search(r'(?:https?://(?:www\.)?(?:twitter|x)\.com/)?@?([a-zA-Z0-9_]{1,15})', text)
    if match:
        uname = match.group(1)
        if len(uname) >= 3 and not uname.lower() in ['http', 'https', 'com', 'twitter', 'x']:
            return uname
    
    parts = re.split(r'[:|,\s\t]+', text)
    for part in parts:
        part_clean = part.replace('@', '').strip()
        if 3 <= len(part_clean) <= 15 and re.match(r'^[a-zA-Z0-9_]+$', part_clean):
            if not part_clean.isdigit():
                return part_clean
    return None

def extract_auth_token(text):
    text = text.strip()
    match = re.search(r'auth_token=([a-zA-Z0-9_-]+)', text)
    if match:
        return match.group(1)
    
    clean_text = text.replace('"', '').replace("'", "").split(';')[0].strip()
    if len(clean_text) >= 20:
        return clean_text
    return text

def check_status_by_username(username):
    if not username or username == 'N/A':
        return 'suspended'
    
    clean_username = username.replace('@', '').strip()
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9'
    }
    
    try:
        url = f"https://x.com/{clean_username}"
        res = requests.get(url, headers=headers, timeout=6)
        if res.status_code == 200:
            html = res.text.lower()
            if "account suspended" in html or "this account doesn’t exist" in html or "user not found" in html:
                return 'suspended'
            return 'active'
        elif res.status_code == 404:
            return 'suspended'
    except Exception:
        pass

    return 'active'

def process_file_or_text_usernames(message):
    usernames_found = []
    if message.content_type == 'document':
        try:
            file_info = bot.get_file(message.document.file_id)
            downloaded_file = bot.download_file(file_info.file_path)
            file_name = message.document.file_name.lower()
            
            if file_name.endswith('.xlsx'):
                wb = openpyxl.load_workbook(io.BytesIO(downloaded_file))
                sheet = wb.active
                for row in sheet.iter_rows(values_only=True):
                    if not any(row):
                        continue
                    row_list = [str(c) if c is not None else "" for c in row]
                    if row_list and row_list[0]:
                        u = extract_username(row_list[0])
                        if u:
                            usernames_found.append(u)
            else:
                content = downloaded_file.decode('utf-8', errors='ignore')
                for line in content.splitlines():
                    u = extract_username(line)
                    if u:
                        usernames_found.append(u)
        except Exception:
            pass
    elif message.content_type == 'text':
        for line in message.text.splitlines():
            u = extract_username(line)
            if u:
                usernames_found.append(u)
                
    seen = set()
    return [x for x in usernames_found if not (x in seen or seen.add(x))]

def parse_full_accounts_file(message):
    rows_data = []
    if message.content_type == 'document':
        try:
            file_info = bot.get_file(message.document.file_id)
            downloaded_file = bot.download_file(file_info.file_path)
            file_name = message.document.file_name.lower()
            
            if file_name.endswith('.xlsx'):
                wb = openpyxl.load_workbook(io.BytesIO(downloaded_file))
                sheet = wb.active
                for row in sheet.iter_rows(values_only=True):
                    if not any(row):
                        continue
                    row_list = [str(c) if c is not None else "" for c in row]
                    uname = extract_username(row_list[0]) if row_list and row_list[0] else None
                    rows_data.append({'row': row_list, 'username': uname})
            else:
                content = downloaded_file.decode('utf-8', errors='ignore')
                for line in content.splitlines():
                    if not line.strip():
                        continue
                    parts = re.split(r'[:|,\s\t]+', line.strip())
                    uname = extract_username(parts[0]) if parts else None
                    rows_data.append({'row': [line.strip()], 'username': uname})
        except Exception:
            pass
    elif message.content_type == 'text':
        for line in message.text.splitlines():
            if not line.strip():
                continue
            parts = re.split(r'[:|,\s\t]+', line.strip())
            uname = extract_username(parts[0]) if parts else None
            rows_data.append({'row': [line.strip()], 'username': uname})
    return rows_data

def approve_single_account(acc):
    if acc.get('status') == 'pending':
        acc['status'] = 'approved'
        target_uid = acc['user_id']
        rw = SETTINGS['reward_tw_token'] if acc.get('task_name') == SETTINGS['task1_name'] else SETTINGS['reward_tw_2fa']
        
        u_data = get_user_data(target_uid)
        u_data['balance'] += rw
        u_data['total_earned'] += rw
        u_data['completed_tasks'] += 1
        
        if SETTINGS.get('ref_enabled', True):
            referrer_id = u_data.get('referred_by')
            if referrer_id and referrer_id in users:
                pct = SETTINGS.get('ref_commission_pct', 10.0)
                commission = rw * (pct / 100.0)
                ref_user = get_user_data(referrer_id)
                ref_user['balance'] += commission
                ref_user['total_earned'] += commission
                ref_user['ref_earned'] = ref_user.get('ref_earned', 0.0) + commission
                try:
                    bot.send_message(referrer_id, f"👥 **Referral Commission!**\nYour referral completed a task, you earned **${commission:.4f}** commission!")
                except Exception:
                    pass

        try:
            bot.send_message(target_uid, f"✅ Your submitted account ({acc.get('username')}) has been approved! ${rw:.4f} added to your balance.")
        except Exception:
            pass
        return True
    return False

def reject_single_account(acc):
    if acc.get('status') == 'pending':
        acc['status'] = 'rejected'
        target_uid = acc['user_id']
        if acc.get('username'):
            rejected_history_db.add(acc.get('username').lower().strip())
        try:
            bot.send_message(target_uid, f"❌ Your submitted account ({acc.get('username')}) has been rejected by admin.")
        except Exception:
            pass
        return True
    return False

def distribute_top_rewards():
    sorted_u = sorted(users.items(), key=lambda x: x[1].get('completed_tasks', 0), reverse=True)
    rewards = SETTINGS.get('top_rewards', {1: 1.00, 2: 0.50, 3: 0.30, 4: 0.20, 5: 0.10})
    
    rewarded_text = "🎉 **Top Leaderboard Winners & Rewards Added:**\n\n"
    count = 0
    for idx, (uid, udata) in enumerate(sorted_u[:5], 1):
        bonus = rewards.get(idx, 0.0)
        if bonus > 0 and udata.get('completed_tasks', 0) > 0:
            udata['balance'] += bonus
            udata['total_earned'] += bonus
            rewarded_text += f"{idx}. {udata['name']} (`{uid}`) - Bonus: `${bonus:.2f}`\n"
            try:
                bot.send_message(uid, f"🏆 Congratulations! You ranked **#{idx}** on the Top Leaderboard and received a bonus of **${bonus:.2f}**!")
            except Exception:
                pass
            count += 1
            
    for uid in users:
        users[uid]['completed_tasks'] = 0
        
    SETTINGS['top_reset_timestamp'] = time.time() + (SETTINGS.get('top_reset_interval_mins', 1440) * 60)
    return rewarded_text if count > 0 else "❌ No active users with completed tasks to reward."

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    if user_id in blocked_users:
        bot.send_message(user_id, "❌ You are blocked!")
        return

    name = message.from_user.first_name or "User"
    is_new_user = user_id not in users
    u_data = get_user_data(user_id, name)

    args = message.text.split()
    if is_new_user and len(args) > 1 and args[1].startswith('ref_'):
        try:
            ref_id = int(args[1].replace('ref_', ''))
            if ref_id != user_id and ref_id in users and not u_data.get('referred_by'):
                u_data['referred_by'] = ref_id
                ref_user = get_user_data(ref_id)
                ref_user['referral_count'] = ref_user.get('referral_count', 0) + 1
                if 'referrals_list' not in ref_user:
                    ref_user['referrals_list'] = []
                ref_user['referrals_list'].append({'uid': user_id, 'time': time.time()})
                
                try:
                    bot.send_message(ref_id, f"👥 **Referral Notification!**\nA new member joined from your referral link: {name}")
                except Exception:
                    pass
        except Exception:
            pass

    if not is_subscribed(user_id):
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(telebot.types.InlineKeyboardButton("Join Channel", url=f"https://t.me/{CHANNEL_USERNAME.replace('@', '')}"))
        bot.send_message(user_id, f"You must join {CHANNEL_USERNAME} to use this bot!", reply_markup=markup)
        return

    bot.send_message(user_id, "Welcome to Taskly Bot! Select an option below:", reply_markup=main_keyboard(user_id))

@bot.message_handler(content_types=['text', 'photo', 'video', 'document'], func=lambda m: True)
def handle_all_messages(message):
    global submitted_accounts, rejected_accounts_db, withdraw_requests, videos_list, downloaded_status, blocked_users, lifetime_usernames, rejected_history_db
    user_id = message.from_user.id
    if user_id in blocked_users:
        return

    if user_id == ADMIN_ID and message.content_type == 'text':
        t_clean = message.text.strip()
        if t_clean in ["👑 Admin Panel", "Admin Panel", "📊 Database Stats", "🏠 Main Menu", "❌ Cancel"]:
            user_steps.pop(ADMIN_ID, None)
            if t_clean in ["👑 Admin Panel", "Admin Panel"]:
                bot.send_message(ADMIN_ID, "👑 **Admin Panel - Control Center**", reply_markup=admin_panel_keyboard(), parse_mode="Markdown")
                return
            elif t_clean == "📊 Database Stats":
                bot.send_message(ADMIN_ID, "📊 **Database & Accounts Management**\n\nChoose an option below:", reply_markup=database_stats_keyboard(), parse_mode="Markdown")
                return
            elif t_clean in ["🏠 Main Menu", "❌ Cancel"]:
                active_mails.pop(user_id, None)
                user_acc_data.pop(user_id, None)
                bot.send_message(user_id, "❌ Returned to Main Menu:", reply_markup=main_keyboard(user_id))
                return

    if user_id == ADMIN_ID:
        admin_step = user_steps.get(ADMIN_ID)
        
        if admin_step == 'awaiting_batch_pin':
            user_steps.pop(ADMIN_ID, None)
            entered_pin = message.text.strip()
            correct_pin = str(SETTINGS.get('admin_pin', '4875'))
            if entered_pin == correct_pin:
                bot.send_message(ADMIN_ID, "🔓 **Password correct!** Panel unlocked:", reply_markup=batch_panel_keyboard(), parse_mode="Markdown")
            else:
                bot.send_message(ADMIN_ID, "❌ **Incorrect PIN!** Access denied. Click the button to try again:", reply_markup=admin_panel_keyboard(), parse_mode="Markdown")
            return

        if admin_step == 'admin_awaiting_lifetime_history':
            usernames = process_file_or_text_usernames(message)
            user_steps.pop(ADMIN_ID, None)
            
            if not usernames:
                bot.send_message(ADMIN_ID, "❌ No valid usernames found in the file or text! Please try again:", reply_markup=database_stats_keyboard())
                return
            
            for u in usernames:
                lifetime_usernames.add(u.lower())
            
            bot.send_message(ADMIN_ID, f"✅ Successfully added `{len(usernames)}` usernames to the Lifetime Database!\nTotal Lifetime Usernames stored: `{len(lifetime_usernames)}`", reply_markup=database_stats_keyboard(), parse_mode="Markdown")
            return

        elif admin_step == 'admin_awaiting_filter_file':
            rows_data = parse_full_accounts_file(message)
            user_steps.pop(ADMIN_ID, None)
            
            if not rows_data:
                bot.send_message(ADMIN_ID, "❌ No data found in the uploaded file/text! Please try again:", reply_markup=database_stats_keyboard())
                return
            
            all_known = set(lifetime_usernames)
            for acc in submitted_accounts:
                if acc.get('username'):
                    all_known.add(acc.get('username').lower().strip())

            new_rows = []
            duplicate_rows = []

            for item in rows_data:
                uname = item['username']
                if uname and uname.lower().strip() in all_known:
                    duplicate_rows.append(item['row'])
                else:
                    new_rows.append(item['row'])
                    if uname:
                        lifetime_usernames.add(uname.lower().strip())

            wb_new = openpyxl.Workbook()
            ws_new = wb_new.active
            ws_new.title = "New_Accounts"
            for r in new_rows:
                ws_new.append(r)
            
            file_new = io.BytesIO()
            wb_new.save(file_new)
            file_new.seek(0)
            file_new.name = "new_accounts.xlsx"

            wb_dup = openpyxl.Workbook()
            ws_dup = wb_dup.active
            ws_dup.title = "Duplicate_Accounts"
            for r in duplicate_rows:
                ws_dup.append(r)
            
            file_dup = io.BytesIO()
            wb_dup.save(file_dup)
            file_dup.seek(0)
            file_dup.name = "duplicate_old_accounts.xlsx"

            summary_msg = (
                f"📊 **Account Filter & Split Summary:**\n"
                f"• Total Checked: `{len(rows_data)}`\n"
                f"• Brand New Accounts: `{len(new_rows)}`\n"
                f"• Already Existed (Old/Duplicate): `{len(duplicate_rows)}`"
            )
            bot.send_message(ADMIN_ID, summary_msg, parse_mode="Markdown")

            if new_rows:
                bot.send_document(ADMIN_ID, file_new, caption="🟢 **New Accounts Excel File**")
            if duplicate_rows:
                bot.send_document(ADMIN_ID, file_dup, caption="🔴 **Already Submitted / Old Accounts Excel File**")

            bot.send_message(ADMIN_ID, "✅ Filtering and splitting completed successfully!", reply_markup=database_stats_keyboard())
            return

        elif admin_step == 'admin_awaiting_custom_usernames':
            rows_data = parse_full_accounts_file(message)
            user_steps.pop(ADMIN_ID, None)
            
            if not rows_data:
                bot.send_message(ADMIN_ID, "❌ No valid accounts found!", reply_markup=admin_panel_keyboard())
                return

            msg = bot.send_message(ADMIN_ID, f"⏳ Checking {len(rows_data)} accounts for duplicates and live status...")
            
            good_accounts = []
            suspended_accounts = []
            seen_in_this_file = set()

            all_known_usernames = set(lifetime_usernames)
            all_known_tokens = set()
            all_known_2fa = set()

            for acc in submitted_accounts:
                if acc.get('username'):
                    all_known_usernames.add(acc.get('username').lower().strip())
                if acc.get('token') and acc.get('token') != 'N/A':
                    all_known_tokens.add(acc.get('token').strip())
                if acc.get('2fa') and acc.get('2fa') != 'N/A':
                    all_known_2fa.add(acc.get('2fa').upper().strip())

            for item in rows_data:
                uname = item['username']
                clean_uname = uname.lower().strip() if uname else ''
                row_str = " ".join([str(x) for x in item['row']])
                
                token_found = extract_auth_token(row_str)
                twofa_matches = re.findall(r'\b[A-Z0-9]{16}\b', row_str.upper())
                twofa_found = twofa_matches[0] if twofa_matches else None

                if clean_uname and clean_uname in rejected_history_db:
                    item_copy = {
                        'username': item.get('username'),
                        'row': list(item.get('row', []))
                    }
                    if len(item_copy['row']) > 0:
                        item_copy['row'][0] = alter_string_slightly(item_copy['row'][0])
                    if len(item_copy['row']) > 1:
                        item_copy['row'][1] = alter_string_slightly(item_copy['row'][1])
                    suspended_accounts.append(item_copy)
                    continue

                is_dup = False
                if uname and clean_uname in all_known_usernames:
                    is_dup = True
                if token_found and token_found in all_known_tokens:
                    is_dup = True
                if twofa_found and twofa_found in all_known_2fa:
                    is_dup = True

                identifier = clean_uname + '_' + (token_found if token_found else '')
                if identifier in seen_in_this_file:
                    is_dup = True
                else:
                    seen_in_this_file.add(identifier)

                if is_dup:
                    suspended_accounts.append(item)
                    continue

                if uname:
                    st = check_status_by_username(uname)
                    if st == 'active':
                        good_accounts.append(item)
                        all_known_usernames.add(clean_uname)
                        if token_found: all_known_tokens.add(token_found)
                        if twofa_found: all_known_2fa.add(twofa_found)
                    else:
                        suspended_accounts.append(item)
                else:
                    suspended_accounts.append(item)
                time.sleep(0.05)

            pct = SETTINGS.get('custom_check_reject_pct', 3.5)
            reject_enabled = SETTINGS.get('custom_check_reject_enabled', True)

            if reject_enabled and pct > 0 and good_accounts:
                total_good = len(good_accounts)
                force_reject_count = int(round(total_good * (pct / 100.0)))
                force_reject_count = max(0, min(force_reject_count, total_good))

                if force_reject_count > 0:
                    selected_to_reject = random.sample(good_accounts, force_reject_count)
                    new_good_accs = []
                    for item in good_accounts:
                        if item in selected_to_reject:
                            if item.get('username'):
                                rejected_history_db.add(item.get('username').lower().strip())
                                
                            item_copy = {
                                'username': item.get('username'),
                                'row': list(item.get('row', []))
                            }
                            if len(item_copy['row']) > 0:
                                item_copy['row'][0] = alter_string_slightly(item_copy['row'][0])
                            if len(item_copy['row']) > 1:
                                item_copy['row'][1] = alter_string_slightly(item_copy['row'][1])
                            suspended_accounts.append(item_copy)
                        else:
                            new_good_accs.append(item)
                    good_accounts = new_good_accs

            bot.delete_message(ADMIN_ID, msg.message_id)

            all_accs = good_accounts + suspended_accounts
            max_len = max([len(acc['row']) for acc in all_accs]) if all_accs else 2
            out_headers = []
            for i in range(max_len):
                if i == 0: out_headers.append("USERNAME")
                elif i == 1: out_headers.append("PASSWORD")
                elif i == 2: out_headers.append("2FA KEY")
                elif i == 3: out_headers.append("AUTH TOKEN")
                else: out_headers.append(f"COLUMN {i+1}")

            wb_good = openpyxl.Workbook()
            ws_good = wb_good.active
            ws_good.title = "Good_Accounts"
            ws_good.append(list(out_headers) + ["STATUS"])
            for acc in good_accounts:
                ws_good.append(list(acc['row']) + ["Active / Good"])
            
            file_good = io.BytesIO()
            wb_good.save(file_good)
            file_good.seek(0)
            file_good.name = "good_twitter_accounts.xlsx"

            summary_text = (
                f"📊 **Custom Bulk Username & Duplicate Check Summary:**\n"
                f"• Total Checked: `{len(rows_data)}`\n"
                f"• Good/Active: `{len(good_accounts)}`\n"
                f"• Rejected (Duplicate/Suspended): `{len(suspended_accounts)}`"
            )
            bot.send_message(ADMIN_ID, summary_text, parse_mode="Markdown")

            if good_accounts:
                bot.send_document(ADMIN_ID, file_good, caption="🟢 **Good / Active Accounts Excel**")

            if suspended_accounts:
                wb_sus = openpyxl.Workbook()
                ws_sus = wb_sus.active
                ws_sus.title = "Rejected_Accounts"
                ws_sus.append(list(out_headers) + ["REASON / STATUS"])
                for acc in suspended_accounts:
                    ws_sus.append(list(acc['row']) + ["Rejected (Duplicate or Suspended)"])
                
                file_sus = io.BytesIO()
                wb_sus.save(file_sus)
                file_sus.seek(0)
                file_sus.name = "suspended_twitter_accounts.xlsx"
                bot.send_document(ADMIN_ID, file_sus, caption="🔴 **Rejected / Suspended / Duplicate Accounts Excel**")

            bot.send_message(ADMIN_ID, "✅ Account check completed!", reply_markup=admin_panel_keyboard())
            return

        if admin_step and admin_step.startswith('admin_awaiting_payment_screenshot_'):
            idx_str = admin_step.replace('admin_awaiting_payment_screenshot_', '')
            user_steps.pop(ADMIN_ID, None)
            try:
                idx = int(idx_str)
                if idx < len(withdraw_requests):
                    req = withdraw_requests[idx]
                    req['status'] = 'paid'
                    target_uid = req['user_id']
                    bdt_amount = req['amount_bdt']
                    method = req['method']
                    
                    if message.content_type == 'photo':
                        photo_id = message.photo[-1].file_id
                        try:
                            bot.send_photo(target_uid, photo_id, caption=f"✅ Your withdraw request has been successfully paid!\nAmount: ৳{bdt_amount:.2f} ({method})")
                        except Exception:
                            pass
                        bot.send_message(ADMIN_ID, f"✅ Payment successfully completed and screenshot sent to the user!", reply_markup=admin_panel_keyboard())
                    else:
                        try:
                            bot.send_message(target_uid, f"✅ Your withdraw request has been successfully paid!\nAmount: ৳{bdt_amount:.2f} ({method})")
                        except Exception:
                            pass
                        bot.send_message(ADMIN_ID, f"✅ Payment successfully completed!", reply_markup=admin_panel_keyboard())
            except Exception:
                bot.send_message(ADMIN_ID, "❌ An error occurred, please try again.", reply_markup=admin_panel_keyboard())
            return

        if admin_step == 'admin_awaiting_video_input':
            if message.content_type == 'video':
                file_id = message.video.file_id
                videos_list.append({'title': 'Tutorial Video', 'type': 'file', 'content': file_id})
                user_steps.pop(ADMIN_ID, None)
                bot.send_message(ADMIN_ID, f"✅ Video file successfully added!", reply_markup=video_mgmt_keyboard())
                return
            elif message.content_type == 'text':
                txt = message.text.strip()
                if txt.startswith("http"):
                    videos_list.append({'title': 'Tutorial Video', 'type': 'url', 'content': txt})
                    user_steps.pop(ADMIN_ID, None)
                    bot.send_message(ADMIN_ID, f"✅ Video link successfully added!", reply_markup=video_mgmt_keyboard())
                    return
                else:
                    bot.send_message(ADMIN_ID, "❌ Please provide a valid video link (http...) or upload a video file:")
                    return

        if admin_step == 'admin_user_mgmt_search':
            user_steps.pop(ADMIN_ID, None)
            try:
                target_uid = int(message.text.strip())
                if target_uid in users:
                    u_data = get_user_data(target_uid)
                    st = "🔴 Blocked" if target_uid in blocked_users else "🟢 Active"
                    markup = telebot.types.InlineKeyboardMarkup()
                    if target_uid in blocked_users:
                        markup.add(telebot.types.InlineKeyboardButton("🟢 Unblock User", callback_data=f"adm_unblock_{target_uid}"))
                    else:
                        markup.add(telebot.types.InlineKeyboardButton("🔴 Block User", callback_data=f"adm_block_{target_uid}"))
                    markup.add(telebot.types.InlineKeyboardButton("💰 Edit Balance", callback_data=f"adm_edit_bal_{target_uid}"))

                    msg_txt = (
                        f"👤 **User Profile Info:**\n\n"
                        f"• Name: {u_data.get('name')}\n"
                        f"• UID: `{target_uid}`\n"
                        f"• Status: `{st}`\n"
                        f"• Current Balance: `${u_data.get('balance', 0.0):.4f}`\n"
                        f"• Total Lifetime Earned: `${u_data.get('total_earned', 0.0):.4f}`\n"
                        f"• Completed Tasks: {u_data.get('completed_tasks', 0)}\n"
                        f"• Total Referrals: {u_data.get('referral_count', 0)}"
                    )
                    bot.send_message(ADMIN_ID, msg_txt, reply_markup=markup, parse_mode="Markdown")
                else:
                    bot.send_message(ADMIN_ID, f"❌ No registered user found with this UID (`{target_uid}`)!", reply_markup=admin_panel_keyboard())
            except ValueError:
                bot.send_message(ADMIN_ID, "❌ Please send a valid numeric UID:", reply_markup=admin_panel_keyboard())
            return

        elif admin_step and admin_step.startswith('adm_set_bal_'):
            try:
                target_uid = int(admin_step.replace('adm_set_bal_', ''))
                new_bal = float(message.text.strip())
                if target_uid in users:
                    users[target_uid]['balance'] = new_bal
                    user_steps.pop(ADMIN_ID, None)
                    bot.send_message(ADMIN_ID, f"✅ User (`{target_uid}`) balance successfully updated to **${new_bal:.4f}**.", reply_markup=admin_panel_keyboard(), parse_mode="Markdown")
                    try:
                        bot.send_message(target_uid, f"💰 Your balance was updated by admin. Current balance: **${new_bal:.4f}**", parse_mode="Markdown")
                    except Exception:
                        pass
                else:
                    user_steps.pop(ADMIN_ID, None)
                    bot.send_message(ADMIN_ID, "❌ User not found!", reply_markup=admin_panel_keyboard())
            except ValueError:
                bot.send_message(ADMIN_ID, "❌ Please send a valid number (e.g. `5.50`):")
            return

        elif admin_step == 'admin_broadcast_msg':
            user_steps.pop(ADMIN_ID, None)
            success = 0
            for uid in users:
                try:
                    bot.send_message(uid, f"📢 **Announcement:**\n\n{message.text}", parse_mode="Markdown")
                    success += 1
                except Exception:
                    pass
            bot.send_message(ADMIN_ID, f"✅ Broadcast sent successfully to {success} users!", reply_markup=admin_panel_keyboard())
            return

        elif admin_step == 'admin_search_uid_input':
            user_steps.pop(ADMIN_ID, None)
            search_query = message.text.strip()
            found_accounts = [acc for acc in submitted_accounts if str(search_query) in str(acc.get('user_id')) or search_query.lower() in str(acc.get('username')).lower()]
            if not found_accounts:
                bot.send_message(ADMIN_ID, f"❌ No accounts found for query: `{search_query}`", reply_markup=admin_panel_keyboard(), parse_mode="Markdown")
                return
            
            target_uid_found = found_accounts[0]['user_id']
            markup = telebot.types.InlineKeyboardMarkup()
            markup.add(telebot.types.InlineKeyboardButton("✅ Approve All for this User", callback_data=f"app_uid_{target_uid_found}"))
            markup.add(telebot.types.InlineKeyboardButton("❌ Reject All for this User", callback_data=f"rej_uid_{target_uid_found}"))

            summary_text = f"🔍 **Search Results for Query:** `{search_query}`\nTotal Pending/Found: {len(found_accounts)}\nTarget UID: `{target_uid_found}`"
            bot.send_message(ADMIN_ID, summary_text, parse_mode="Markdown", reply_markup=markup)

            for acc in found_accounts:
                idx = submitted_accounts.index(acc)
                btn = telebot.types.InlineKeyboardMarkup()
                btn.add(telebot.types.InlineKeyboardButton("Approve", callback_data=f"app_{idx}"), telebot.types.InlineKeyboardButton("Reject", callback_data=f"rej_{idx}"))
                info = f"User: `{acc['user_id']}`\nStatus: `{acc.get('status')}`\nTask: `{acc.get('task_name')}`\nUsername: `{acc['username']}`\nPassword: `{acc['password']}`\n2FA: `{acc.get('2fa', 'N/A')}`"
                bot.send_message(ADMIN_ID, info, parse_mode="Markdown", reply_markup=btn)
            return

        elif admin_step == 'admin_batch_approve_input':
            user_steps.pop(ADMIN_ID, None)
            usernames = [u.strip().lower() for u in message.text.split()]
            count = 0
            for acc in submitted_accounts:
                if acc.get('status') == 'pending' and acc.get('username', '').lower() in usernames:
                    if approve_single_account(acc):
                        count += 1
            bot.send_message(ADMIN_ID, f"✅ Batch approve completed! Total `{count}` accounts approved.", reply_markup=admin_panel_keyboard(), parse_mode="Markdown")
            return

        elif admin_step == 'admin_batch_reject_input':
            user_steps.pop(ADMIN_ID, None)
            usernames = [u.strip().lower() for u in message.text.split()]
            count = 0
            for acc in submitted_accounts:
                if acc.get('status') == 'pending' and acc.get('username', '').lower() in usernames:
                    if reject_single_account(acc):
                        count += 1
            bot.send_message(ADMIN_ID, f"❌ Batch reject completed! Total `{count}` accounts rejected.", reply_markup=admin_panel_keyboard(), parse_mode="Markdown")
            return

        elif admin_step == 'admin_percentage_approve_input':
            user_steps.pop(ADMIN_ID, None)
            try:
                pct = float(message.text.strip())
                if not (0 <= pct <= 100):
                    bot.send_message(ADMIN_ID, "❌ Percentage must be between 0 and 100.", reply_markup=admin_panel_keyboard())
                    return

                user_pending_dict = {}
                for acc in submitted_accounts:
                    if acc.get('status') == 'pending':
                        uid = acc.get('user_id')
                        if uid not in user_pending_dict:
                            user_pending_dict[uid] = []
                        user_pending_dict[uid].append(acc)

                total_approved = 0
                total_rejected = 0

                for uid, accs in user_pending_dict.items():
                    total_accs = len(accs)
                    approve_count = int(round(total_accs * (pct / 100.0)))
                    approve_count = max(0, min(approve_count, total_accs))

                    for i, acc in enumerate(accs):
                        if i < approve_count:
                            if approve_single_account(acc):
                                total_approved += 1
                        else:
                            if reject_single_account(acc):
                                total_rejected += 1

                bot.send_message(ADMIN_ID, f"✅ Percentage auto-process completed!\n• Approved: `{total_approved}`\n• Rejected: `{total_rejected}`\n• Rate: `{pct}%`", reply_markup=admin_panel_keyboard(), parse_mode="Markdown")
            except ValueError:
                bot.send_message(ADMIN_ID, "❌ Please send a valid number (e.g. `80`):", reply_markup=admin_panel_keyboard())
            return

        elif admin_step == 'admin_percentage_reject_input':
            user_steps.pop(ADMIN_ID, None)
            try:
                pct = float(message.text.strip())
                if not (0 <= pct <= 100):
                    bot.send_message(ADMIN_ID, "❌ Percentage must be between 0 and 100.", reply_markup=admin_panel_keyboard())
                    return

                SETTINGS['custom_check_reject_pct'] = pct

                user_pending_dict = {}
                for acc in submitted_accounts:
                    if acc.get('status') == 'pending':
                        uid = acc.get('user_id')
                        if uid not in user_pending_dict:
                            user_pending_dict[uid] = []
                        user_pending_dict[uid].append(acc)

                total_approved = 0
                total_rejected = 0

                for uid, accs in user_pending_dict.items():
                    total_accs = len(accs)
                    reject_count = int(round(total_accs * (pct / 100.0)))
                    reject_count = max(0, min(reject_count, total_accs))

                    for i, acc in enumerate(accs):
                        if i < reject_count:
                            if reject_single_account(acc):
                                total_rejected += 1
                        else:
                            if approve_single_account(acc):
                                total_approved += 1

                bot.send_message(ADMIN_ID, f"📉 Percentage Reject process completed!\n• New Custom Check Reject Rate updated to: `{pct}%`\n• Pending Rejected: `{total_rejected}`\n• Pending Approved: `{total_approved}`", reply_markup=admin_panel_keyboard(), parse_mode="Markdown")
            except ValueError:
                bot.send_message(ADMIN_ID, "❌ Please send a valid number (e.g. `2` or `5`):", reply_markup=admin_panel_keyboard())
            return

        elif admin_step == 'set_min_withdraw_limit':
            user_steps.pop(ADMIN_ID, None)
            try:
                new_min = float(message.text.strip())
                if new_min < 0:
                    bot.send_message(ADMIN_ID, "❌ Limit cannot be negative.", reply_markup=payment_toggle_keyboard())
                    return
                SETTINGS['min_withdraw_bdt'] = new_min
                bot.send_message(ADMIN_ID, f"✅ Minimum withdraw limit successfully updated to: ৳{new_min:.2f}", reply_markup=payment_toggle_keyboard(), parse_mode="Markdown")
            except ValueError:
                bot.send_message(ADMIN_ID, "❌ Please enter a valid number in BDT (e.g. `10` or `50`):", reply_markup=payment_toggle_keyboard())
            return

        elif admin_step == 'set_report_time_custom':
            user_steps.pop(ADMIN_ID, None)
            SETTINGS['task_report_timer_text'] = message.text.strip()
            bot.send_message(ADMIN_ID, f"✅ Report timer text updated to: `{message.text.strip()}`", reply_markup=task_control_keyboard(), parse_mode="Markdown")
            return

        elif admin_step == 'set_custom_pwd_value':
            user_steps.pop(ADMIN_ID, None)
            SETTINGS['custom_pwd_value'] = message.text
            SETTINGS['pwd_mode'] = 'same'
            bot.send_message(ADMIN_ID, f"✅ Custom/Same password updated to: `{message.text}` (Mode set to Custom)", reply_markup=password_mgmt_keyboard(), parse_mode="Markdown")
            return

        elif admin_step == 'set_ref_commission_pct':
            user_steps.pop(ADMIN_ID, None)
            try:
                pct = float(message.text.strip())
                SETTINGS['ref_commission_pct'] = pct
                bot.send_message(ADMIN_ID, f"✅ Referral commission updated to: `{pct}%`", reply_markup=referral_mgmt_keyboard(), parse_mode="Markdown")
            except ValueError:
                bot.send_message(ADMIN_ID, "❌ Please enter a valid number (e.g. 10 or 15):", reply_markup=referral_mgmt_keyboard())
            return

        elif admin_step == 'set_top_reset_mins_input':
            try:
                mins = int(message.text.strip())
                SETTINGS['top_reset_interval_mins'] = mins
                SETTINGS['top_reset_mode'] = 'custom_minutes'
                SETTINGS['top_reset_timestamp'] = time.time() + (mins * 60)
                user_steps.pop(ADMIN_ID, None)
                bot.send_message(ADMIN_ID, f"✅ Leaderboard reset time updated to every `{mins}` minutes!", reply_markup=top_control_keyboard(), parse_mode="Markdown")
            except ValueError:
                bot.send_message(ADMIN_ID, "❌ Please send a valid number (e.g. 60 or 1440):", reply_markup=top_control_keyboard())
            return

        elif admin_step == 'set_top_rank_rewards':
            try:
                parts = message.text.split()
                r1, r2, r3, r4, r5 = float(parts[0]), float(parts[1]), float(parts[2]), float(parts[3]), float(parts[4])
                SETTINGS['top_rewards'] = {1: r1, 2: r2, 3: r3, 4: r4, 5: r5}
                user_steps.pop(ADMIN_ID, None)
                bot.send_message(ADMIN_ID, f"✅ Rank Rewards Updated!\n1st: `${r1}`\n2nd: `${r2}`\n3rd: `${r3}`\n4th: `${r4}`\n5th: `${r5}`", reply_markup=top_control_keyboard(), parse_mode="Markdown")
            except Exception:
                bot.send_message(ADMIN_ID, "❌ Invalid format! Enter 5 space-separated numbers (e.g. `1.0 0.5 0.3 0.2 0.1`):", reply_markup=top_control_keyboard())
            return

        elif admin_step == 'set_price_t1':
            user_steps.pop(ADMIN_ID, None)
            try:
                SETTINGS['reward_tw_token'] = float(message.text)
                bot.send_message(ADMIN_ID, f"✅ Task 1 reward updated to ${SETTINGS['reward_tw_token']:.4f}", reply_markup=admin_panel_keyboard())
            except ValueError:
                bot.send_message(ADMIN_ID, "❌ Invalid number format!", reply_markup=admin_panel_keyboard())
            return

        elif admin_step == 'set_price_t2':
            user_steps.pop(ADMIN_ID, None)
            try:
                SETTINGS['reward_tw_2fa'] = float(message.text)
                bot.send_message(ADMIN_ID, f"✅ Task 2 reward updated to ${SETTINGS['reward_tw_2fa']:.4f}", reply_markup=admin_panel_keyboard())
            except ValueError:
                bot.send_message(ADMIN_ID, "❌ Invalid number format!", reply_markup=admin_panel_keyboard())
            return

    if message.content_type != 'text':
        return

    text = message.text.strip()

    if text in ["❌ Cancel", "Cancel", "cancel", "Main Menu", "🏠 Main Menu"]:
        active_mails.pop(user_id, None)
        user_steps.pop(user_id, None)
        user_acc_data.pop(user_id, None)
        bot.send_message(user_id, "❌ Returned to Main Menu:", reply_markup=main_keyboard(user_id))
        return

    if user_id == ADMIN_ID:
        if text in ["👑 Admin Panel", "Admin Panel"]:
            bot.send_message(ADMIN_ID, "👑 **Admin Panel - Control Center**", reply_markup=admin_panel_keyboard(), parse_mode="Markdown")
            return

        elif text == "📊 Database Stats":
            bot.send_message(ADMIN_ID, "📊 **Database & Accounts Management**\n\nChoose an option below:", reply_markup=database_stats_keyboard(), parse_mode="Markdown")
            return

        elif text == "📈 View Stats":
            total_lifetime = len(lifetime_usernames)
            total_submitted = len(submitted_accounts)
            pending_accs = sum(1 for a in submitted_accounts if a.get('status') == 'pending')
            approved_accs = sum(1 for a in submitted_accounts if a.get('status') == 'approved')
            stats_msg = (
                f"📊 **Database & Accounts Stats:**\n\n"
                f"• Stored Lifetime Usernames: `{total_lifetime}`\n"
                f"• Total Submitted Accounts: `{total_submitted}`\n"
                f"• Pending Accounts: `{pending_accs}`\n"
                f"• Approved Accounts: `{approved_accs}`"
            )
            bot.send_message(ADMIN_ID, stats_msg, reply_markup=database_stats_keyboard(), parse_mode="Markdown")
            return

        elif text == "📁 Upload Lifetime Excel":
            user_steps[ADMIN_ID] = 'admin_awaiting_lifetime_history'
            bot.send_message(ADMIN_ID, "📁 Send or upload the **Lifetime/Old Work Sheet** (`.xlsx` or text/list) to save in database:", reply_markup=database_stats_keyboard(), parse_mode="Markdown")
            return

        elif text == "🔍 Filter New vs Old Excel":
            user_steps[ADMIN_ID] = 'admin_awaiting_filter_file'
            bot.send_message(ADMIN_ID, "🔍 Send or upload the **New Submitted Sheet** (`.xlsx` or text/list) to filter against lifetime records:", reply_markup=database_stats_keyboard(), parse_mode="Markdown")
            return

        elif text == "📥 Custom Username Check":
            user_steps[ADMIN_ID] = 'admin_awaiting_custom_usernames'
            bot.send_message(ADMIN_ID, "📥 Send or upload the accounts file (`.xlsx` or text). The bot will use the **first column/line** as Username and check for duplicates/dead accounts:", reply_markup=telebot.types.ReplyKeyboardMarkup(resize_keyboard=True).row(telebot.types.KeyboardButton("👑 Admin Panel")))
            return

        elif text == "🔍 Check Accounts via Username":
            if not submitted_accounts:
                bot.send_message(ADMIN_ID, "❌ No submitted accounts found in bot database to check!", reply_markup=admin_panel_keyboard())
                return

            msg = bot.send_message(ADMIN_ID, f"⏳ Checking status for {len(submitted_accounts)} accounts using Usernames, please wait...")
            
            good_accounts = []
            suspended_accounts = []
            
            for acc in submitted_accounts:
                uname = acc.get('username')
                clean_u = uname.lower().strip() if uname else ''
                
                if clean_u and clean_u in rejected_history_db:
                    item_copy = acc.copy()
                    item_copy['username'] = alter_string_slightly(item_copy.get('username', ''))
                    item_copy['password'] = alter_string_slightly(item_copy.get('password', ''))
                    suspended_accounts.append(item_copy)
                    continue

                st = check_status_by_username(uname)
                if st == 'active':
                    good_accounts.append(acc)
                else:
                    suspended_accounts.append(acc)
                time.sleep(0.05)

            pct = SETTINGS.get('custom_check_reject_pct', 3.5)
            reject_enabled = SETTINGS.get('custom_check_reject_enabled', True)

            if reject_enabled and pct > 0 and good_accounts:
                total_good = len(good_accounts)
                force_reject_count = int(round(total_good * (pct / 100.0)))
                force_reject_count = max(0, min(force_reject_count, total_good))

                if force_reject_count > 0:
                    selected_to_reject = random.sample(good_accounts, force_reject_count)
                    new_good_accs = []
                    for acc in good_accounts:
                        if acc in selected_to_reject:
                            if acc.get('username'):
                                rejected_history_db.add(acc.get('username').lower().strip())
                            item_copy = acc.copy()
                            item_copy['username'] = alter_string_slightly(item_copy.get('username', ''))
                            item_copy['password'] = alter_string_slightly(item_copy.get('password', ''))
                            suspended_accounts.append(item_copy)
                        else:
                            new_good_accs.append(acc)
                    good_accounts = new_good_accs

            bot.delete_message(ADMIN_ID, msg.message_id)

            wb_good = openpyxl.Workbook()
            ws_good = wb_good.active
            ws_good.title = "Good_Accounts"
            ws_good.append(["USER ID", "TASK NAME", "USERNAME", "PASSWORD", "2FA KEY", "AUTH TOKEN", "STATUS"])
            for acc in good_accounts:
                ws_good.append([acc.get('user_id'), acc.get('task_name'), acc.get('username'), acc.get('password'), acc.get('2fa'), acc.get('token'), "Active / Good"])
            
            file_good = io.BytesIO()
            wb_good.save(file_good)
            file_good.seek(0)
            file_good.name = "good_twitter_accounts.xlsx"

            summary_text = (
                f"📊 **Username-Based Account Check Summary:**\n"
                f"• Total Checked: `{len(submitted_accounts)}`\n"
                f"• Good/Active: `{len(good_accounts)}`\n"
                f"• Suspended/Dead: `{len(suspended_accounts)}`"
            )
            bot.send_message(ADMIN_ID, summary_text, parse_mode="Markdown")

            if good_accounts:
                bot.send_document(ADMIN_ID, file_good, caption="🟢 **Good / Active Accounts Excel**")

            if suspended_accounts:
                wb_sus = openpyxl.Workbook()
                ws_sus = wb_sus.active
                ws_sus.title = "Suspended_Accounts"
                ws_sus.append(["USER ID", "TASK NAME", "USERNAME", "PASSWORD", "2FA KEY", "AUTH TOKEN", "STATUS"])
                for acc in suspended_accounts:
                    ws_sus.append([acc.get('user_id'), acc.get('task_name'), acc.get('username'), acc.get('password'), acc.get('2fa'), acc.get('token'), "Suspended / Dead"])
                
                file_sus = io.BytesIO()
                wb_sus.save(file_sus)
                file_sus.seek(0)
                file_sus.name = "suspended_twitter_accounts.xlsx"
                bot.send_document(ADMIN_ID, file_sus, caption="🔴 **Suspended / Dead Accounts Excel**")

            bot.send_message(ADMIN_ID, "✅ Account check completed successfully!", reply_markup=admin_panel_keyboard())
            return

        elif text == "📊 Task 1 Excel":
            filtered_accounts = [acc for acc in submitted_accounts if acc.get('task_name') == SETTINGS['task1_name']]
            bot.send_message(ADMIN_ID, f"📊 **Task 1 Accounts Management**\nTotal Saved: `{len(filtered_accounts)}`", reply_markup=excel_task1_menu(), parse_mode="Markdown")
            return

        elif text == "📊 Download Excel: Task 1":
            filtered_accounts = [acc for acc in submitted_accounts if acc.get('task_name') == SETTINGS['task1_name']]
            if not filtered_accounts:
                bot.send_message(ADMIN_ID, "❌ No accounts submitted for Task 1!", reply_markup=excel_task1_menu())
                return
            
            downloaded_status['task1'] = True
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = "Auth_Token_Accounts"
            ws.append(["USER ID", "TASK NAME", "USERNAME", "PASSWORD", "2FA KEY", "AUTH TOKEN", "STATUS"])
            for acc in filtered_accounts:
                ws.append([acc.get('user_id'), acc.get('task_name'), acc.get('username'), acc.get('password'), acc.get('2fa'), acc.get('token'), acc.get('status')])
            
            file_stream = io.BytesIO()
            wb.save(file_stream)
            file_stream.seek(0)
            file_stream.name = "twitter_auth_token_accounts.xlsx"
            bot.send_document(ADMIN_ID, file_stream, caption=f"📊 **Task 1 Excel File (Auth_Token)**\nTotal: {len(filtered_accounts)}\n\n✅ File downloaded successfully. You can now delete them.")
            return

        elif text == "🗑️ Delete Task 1 Accounts":
            if not downloaded_status.get('task1', False):
                bot.send_message(ADMIN_ID, "⚠️ **Warning!** Please download the Excel file first using `📊 Download Excel: Task 1` button before deleting!", reply_markup=excel_task1_menu(), parse_mode="Markdown")
                return
            
            markup = telebot.types.InlineKeyboardMarkup()
            markup.add(telebot.types.InlineKeyboardButton("⚠️ Yes, Delete All", callback_data="conf_del_t1"), telebot.types.InlineKeyboardButton("❌ Cancel", callback_data="cancel_del"))
            bot.send_message(ADMIN_ID, "⚠️ Are you sure you want to delete all Task 1 accounts?", reply_markup=markup)
            return

        elif text == "📊 Task 2 Excel (2FA)":
            filtered_accounts = [acc for acc in submitted_accounts if acc.get('task_name') == SETTINGS['task2_name']]
            bot.send_message(ADMIN_ID, f"📊 **2FA Accounts Management**\nTotal Saved: `{len(filtered_accounts)}`", reply_markup=excel_2fa_menu(), parse_mode="Markdown")
            return

        elif text == "📊 Download Excel: 2FA":
            filtered_accounts = [acc for acc in submitted_accounts if acc.get('task_name') == SETTINGS['task2_name']]
            if not filtered_accounts:
                bot.send_message(ADMIN_ID, "❌ No accounts submitted for Task 2!", reply_markup=excel_2fa_menu())
                return
            
            downloaded_status['task2'] = True
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = "2FA_Accounts"
            ws.append(["USER ID", "TASK NAME", "USERNAME", "PASSWORD", "2FA KEY", "STATUS"])
            for acc in filtered_accounts:
                ws.append([acc.get('user_id'), acc.get('task_name'), acc.get('username'), acc.get('password'), acc.get('2fa'), acc.get('status')])
            
            file_stream = io.BytesIO()
            wb.save(file_stream)
            file_stream.seek(0)
            file_stream.name = "twitter_2fa_accounts.xlsx"
            bot.send_document(ADMIN_ID, file_stream, caption=f"📊 **2FA Accounts File**\nTotal: {len(filtered_accounts)}\n\n✅ File downloaded successfully. You can now delete them.")
            return

        elif text == "🗑️ Delete 2FA Accounts":
            if not downloaded_status.get('task2', False):
                bot.send_message(ADMIN_ID, "⚠️ **Warning!** Please download the Excel file first using `📊 Download Excel: 2FA` button before deleting!", reply_markup=excel_2fa_menu(), parse_mode="Markdown")
                return
            
            markup = telebot.types.InlineKeyboardMarkup()
            markup.add(telebot.types.InlineKeyboardButton("⚠️ Yes, Delete All", callback_data="conf_del_t2"), telebot.types.InlineKeyboardButton("❌ Cancel", callback_data="cancel_del"))
            bot.send_message(ADMIN_ID, "⚠️ Are you sure you want to delete all Task 2 accounts?", reply_markup=markup)
            return

        elif text.startswith("Withdraw Sys:"):
            SETTINGS['withdraw_enabled'] = not SETTINGS['withdraw_enabled']
            bot.send_message(ADMIN_ID, "Withdraw status toggled!", reply_markup=payment_toggle_keyboard())
            return
        elif text.startswith("Bkash:"):
            SETTINGS['bkash_enabled'] = not SETTINGS['bkash_enabled']
            bot.send_message(ADMIN_ID, "Bkash status toggled!", reply_markup=payment_toggle_keyboard())
            return
        elif text.startswith("Nagad:"):
            SETTINGS['nagad_enabled'] = not SETTINGS['nagad_enabled']
            bot.send_message(ADMIN_ID, "Nagad status toggled!", reply_markup=payment_toggle_keyboard())
            return
        elif text.startswith("Binance:"):
            SETTINGS['binance_enabled'] = not SETTINGS['binance_enabled']
            bot.send_message(ADMIN_ID, "Binance status toggled!", reply_markup=payment_toggle_keyboard())
            return

        elif text.startswith("🔄 Toggle Reject Sys:"):
            SETTINGS['custom_check_reject_enabled'] = not SETTINGS.get('custom_check_reject_enabled', True)
            st_txt = "🟢 ON" if SETTINGS['custom_check_reject_enabled'] else "🔴 OFF"
            bot.send_message(ADMIN_ID, f"✅ Reject System successfully toggled to: **{st_txt}**", reply_markup=batch_panel_keyboard(), parse_mode="Markdown")
            return

        elif text == "⚙️ Set Minimum Withdraw Limit":
            user_steps[ADMIN_ID] = 'set_min_withdraw_limit'
            bot.send_message(ADMIN_ID, f"⚙️ Current Minimum Withdraw Limit: ৳{SETTINGS.get('min_withdraw_bdt', 5.0)}\n\n✍️ Send the new minimum withdraw limit in BDT (numbers only, e.g. `10`):", reply_markup=telebot.types.ReplyKeyboardMarkup(resize_keyboard=True).row(telebot.types.KeyboardButton("⚙️ Payment Methods")), parse_mode="Markdown")
            return

        elif text == "👥 User Management":
            user_steps[ADMIN_ID] = 'admin_user_mgmt_search'
            bot.send_message(ADMIN_ID, "🔍 Send the **UID (User ID)** of the user you want to manage or edit balance for:", reply_markup=telebot.types.ReplyKeyboardMarkup(resize_keyboard=True).row(telebot.types.KeyboardButton("👑 Admin Panel")))
            return

        elif text == "👥 Referral Management":
            st_text = "🟢 Active" if SETTINGS.get('ref_enabled', True) else "🔴 Inactive"
            info_ref = (
                f"👥 **Referral Management Panel**\n\n"
                f"• Status: `{st_text}`\n"
                f"• Commission: `{SETTINGS.get('ref_commission_pct', 10.0)}%`\n\n"
                f"Select an option below to modify:"
            )
            bot.send_message(ADMIN_ID, info_ref, reply_markup=referral_mgmt_keyboard(), parse_mode="Markdown")
            return

        elif text.startswith("Toggle Referral:"):
            SETTINGS['ref_enabled'] = not SETTINGS.get('ref_enabled', True)
            bot.send_message(ADMIN_ID, "Referral status toggled!", reply_markup=referral_mgmt_keyboard())
            return

        elif text == "💰 Set Referral Commission %":
            user_steps[ADMIN_ID] = 'set_ref_commission_pct'
            bot.send_message(ADMIN_ID, "💰 Send referral commission percentage (%) in numbers only (e.g. `10` or `15`):", reply_markup=telebot.types.ReplyKeyboardMarkup(resize_keyboard=True).row(telebot.types.KeyboardButton("👥 Referral Management")), parse_mode="Markdown")
            return

        elif text == "🔐 Password Management":
            info_pwd = (
                f"🔐 **Password Management Panel**\n\n"
                f"• Current Mode: `{SETTINGS.get('pwd_mode')}`\n"
                f"• Target Task: `{SETTINGS.get('pwd_target_task')}`\n"
                f"• Custom Password Value: `{SETTINGS.get('custom_pwd_value')}`\n\n"
                f"Select password mode or target task below:"
            )
            bot.send_message(ADMIN_ID, info_pwd, reply_markup=password_mgmt_keyboard(), parse_mode="Markdown")
            return

        elif text in ["Mode: ✅ Random", "Mode: Random"]:
            SETTINGS['pwd_mode'] = 'random'
            bot.send_message(ADMIN_ID, "✅ Password Mode set to: **Random**", reply_markup=password_mgmt_keyboard(), parse_mode="Markdown")
            return

        elif text in ["Mode: ✅ Random + Date", "Mode: Random + Date"]:
            SETTINGS['pwd_mode'] = 'random_date'
            bot.send_message(ADMIN_ID, "✅ Password Mode set to: **Random + Date**", reply_markup=password_mgmt_keyboard(), parse_mode="Markdown")
            return

        elif text in ["Mode: ✅ Custom / Same", "Mode: Custom / Same"]:
            SETTINGS['pwd_mode'] = 'same'
            bot.send_message(ADMIN_ID, "✅ Password Mode set to: **Custom / Same**", reply_markup=password_mgmt_keyboard(), parse_mode="Markdown")
            return

        elif text.startswith("🔄 Target Task:") or text.startswith("Target Task:"):
            current_target = SETTINGS.get('pwd_target_task', 'BOTH')
            if current_target == 'BOTH':
                SETTINGS['pwd_target_task'] = 'task1'
                new_t = 'Task 1'
            elif current_target == 'task1':
                SETTINGS['pwd_target_task'] = 'task2'
                new_t = 'Task 2'
            else:
                SETTINGS['pwd_target_task'] = 'BOTH'
                new_t = 'BOTH'
            bot.send_message(ADMIN_ID, f"✅ Password Target Task changed to: **{new_t}**", reply_markup=password_mgmt_keyboard(), parse_mode="Markdown")
            return

        elif text == "✍️ Set Custom Password":
            user_steps[ADMIN_ID] = 'set_custom_pwd_value'
            bot.send_message(ADMIN_ID, "✍️ Send the new custom password:", reply_markup=telebot.types.ReplyKeyboardMarkup(resize_keyboard=True).row(telebot.types.KeyboardButton("🔐 Password Management")), parse_mode="Markdown")
            return

        elif text.startswith("Toggle Task 1:"):
            SETTINGS['tw_token_enabled'] = not SETTINGS.get('tw_token_enabled', True)
            bot.send_message(ADMIN_ID, "Task 1 status toggled!", reply_markup=task_control_keyboard())
            return

        elif text.startswith("Toggle Task 2:"):
            SETTINGS['tw_2fa_enabled'] = not SETTINGS.get('tw_2fa_enabled', True)
            bot.send_message(ADMIN_ID, "Task 2 status toggled!", reply_markup=task_control_keyboard())
            return

        elif text == "⏱️ Set Report Timer Text":
            user_steps[ADMIN_ID] = 'set_report_time_custom'
            bot.send_message(ADMIN_ID, "⏱️ Send report timer text (e.g., `Every 30 minutes`):", reply_markup=telebot.types.ReplyKeyboardMarkup(resize_keyboard=True).row(telebot.types.KeyboardButton("🛠️ Task Control")))
            return

        elif text == "🎬 Video Management":
            bot.send_message(ADMIN_ID, f"🎬 **Video Management Panel**\nTotal Videos: `{len(videos_list)}`", reply_markup=video_mgmt_keyboard(), parse_mode="Markdown")
            return

        elif text == "➕ Add Video File / Link":
            user_steps[ADMIN_ID] = 'admin_awaiting_video_input'
            bot.send_message(ADMIN_ID, "🎬 Send a YouTube link or upload a video file for tutorial:", reply_markup=video_mgmt_keyboard(), parse_mode="Markdown")
            return

        elif text == "🗑️ Remove All Videos":
            videos_list.clear()
            bot.send_message(ADMIN_ID, "🗑️ All videos successfully removed!", reply_markup=video_mgmt_keyboard())
            return

        elif text == "🔍 Search UID/Username":
            user_steps[ADMIN_ID] = 'admin_search_uid_input'
            bot.send_message(ADMIN_ID, "🔍 Send the UID or Username you want to search:", reply_markup=telebot.types.ReplyKeyboardMarkup(resize_keyboard=True).row(telebot.types.KeyboardButton("👑 Admin Panel")))
            return

        elif text == "⚡ Batch Approve / Percentage":
            user_steps[ADMIN_ID] = 'awaiting_batch_pin'
            bot.send_message(ADMIN_ID, "🔐 **Enter PIN Code:** Please enter your Admin PIN to access the Batch Approve Panel:", reply_markup=telebot.types.ReplyKeyboardMarkup(resize_keyboard=True).row(telebot.types.KeyboardButton("👑 Admin Panel")), parse_mode="Markdown")
            return

        elif text == "✅ Batch Approve Usernames":
            user_steps[ADMIN_ID] = 'admin_batch_approve_input'
            bot.send_message(ADMIN_ID, "✍️ Send usernames separated by space to approve (e.g., `tracy78kn arif96xo`):", reply_markup=telebot.types.ReplyKeyboardMarkup(resize_keyboard=True).row(telebot.types.KeyboardButton("👑 Admin Panel")))
            return

        elif text == "❌ Batch Reject Usernames":
            user_steps[ADMIN_ID] = 'admin_batch_reject_input'
            bot.send_message(ADMIN_ID, "✍️ Send usernames separated by space to reject (e.g., `tracy78kn arif96xo`):", reply_markup=telebot.types.ReplyKeyboardMarkup(resize_keyboard=True).row(telebot.types.KeyboardButton("👑 Admin Panel")))
            return

        elif text == "📊 Percentage Auto Process":
            user_steps[ADMIN_ID] = 'admin_percentage_approve_input'
            bot.send_message(ADMIN_ID, "📊 Send the percentage (%) of pending accounts to approve (e.g., `80` will approve 80% and reject 20% for each user):", reply_markup=telebot.types.ReplyKeyboardMarkup(resize_keyboard=True).row(telebot.types.KeyboardButton("👑 Admin Panel")), parse_mode="Markdown")
            return

        elif text == "📉 Percentage Reject Process":
            user_steps[ADMIN_ID] = 'admin_percentage_reject_input'
            bot.send_message(ADMIN_ID, f"📉 Current Default Custom Check Reject Rate: `{SETTINGS.get('custom_check_reject_pct', 3.5)}%`\n\nSend the new percentage (%) of rejection rate (e.g., `2` for 2%, `5` for 5%):", reply_markup=telebot.types.ReplyKeyboardMarkup(resize_keyboard=True).row(telebot.types.KeyboardButton("👑 Admin Panel")), parse_mode="Markdown")
            return

        elif text == "🏆 Top Control":
            st_text = "🟢 Active" if SETTINGS.get('top_enabled', True) else "🔴 Inactive"
            mode = SETTINGS.get('top_reset_mode')
            if mode == 'daily_10pm':
                mode_text = "Daily 10:00 PM"
            elif mode == 'sunday_10pm':
                mode_text = "Sunday 10:00 PM"
            else:
                mode_text = f"Every {SETTINGS.get('top_reset_interval_mins', 1440)} mins"

            rw = SETTINGS.get('top_rewards', {})
            info_msg = (
                f"🏆 **Top Leaderboard Management**\n\n"
                f"• Status: `{st_text}`\n"
                f"• Reset Schedule: `{mode_text}`\n"
                f"• Rewards list:\n"
                f"  🥇 Rank 1: `${rw.get(1, 0):.2f}`\n"
                f"  🥈 Rank 2: `${rw.get(2, 0):.2f}`\n"
                f"  🥉 Rank 3: `${rw.get(3, 0):.2f}`\n"
                f"  4️⃣ Rank 4: `${rw.get(4, 0):.2f}`\n"
                f"  5️⃣ Rank 5: `${rw.get(5, 0):.2f}`\n"
            )
            bot.send_message(ADMIN_ID, info_msg, reply_markup=top_control_keyboard(), parse_mode="Markdown")
            return

        elif text.startswith("Toggle Leaderboard:"):
            SETTINGS['top_enabled'] = not SETTINGS.get('top_enabled', True)
            bot.send_message(ADMIN_ID, "Leaderboard Status Toggled!", reply_markup=top_control_keyboard())
            return

        elif text.startswith("Reset Schedule:"):
            current_mode = SETTINGS.get('top_reset_mode', 'daily_10pm')
            if current_mode == 'daily_10pm':
                SETTINGS['top_reset_mode'] = 'sunday_10pm'
                bot.send_message(ADMIN_ID, "✅ Reset schedule changed to: **Sunday 10:00 PM**", reply_markup=top_control_keyboard(), parse_mode="Markdown")
            elif current_mode == 'sunday_10pm':
                SETTINGS['top_reset_mode'] = 'daily_10pm'
                bot.send_message(ADMIN_ID, "✅ Reset schedule changed to: **Daily 10:00 PM**", reply_markup=top_control_keyboard(), parse_mode="Markdown")
            else:
                SETTINGS['top_reset_mode'] = 'daily_10pm'
                bot.send_message(ADMIN_ID, "✅ Reset schedule changed to: **Daily 10:00 PM**", reply_markup=top_control_keyboard(), parse_mode="Markdown")
            return

        elif text == "⏱️ Set Reset Minutes":
            user_steps[ADMIN_ID] = 'set_top_reset_mins_input'
            bot.send_message(ADMIN_ID, "⏱️ Send reset interval in minutes (e.g., `30`, `60`, or `1440`):", reply_markup=telebot.types.ReplyKeyboardMarkup(resize_keyboard=True).row(telebot.types.KeyboardButton("🏆 Top Control")), parse_mode="Markdown")
            return

        elif text == "🎁 Distribute Rewards & Reset Now":
            res = distribute_top_rewards()
            bot.send_message(ADMIN_ID, res, reply_markup=top_control_keyboard(), parse_mode="Markdown")
            return

        elif text == "💰 Edit Rank Rewards":
            user_steps[ADMIN_ID] = 'set_top_rank_rewards'
            bot.send_message(ADMIN_ID, "💰 Send bonus amounts for ranks 1 to 5 separated by space:\n\n**Example:** `1.00 0.50 0.30 0.20 0.10`", reply_markup=telebot.types.ReplyKeyboardMarkup(resize_keyboard=True).row(telebot.types.KeyboardButton("🏆 Top Control")), parse_mode="Markdown")
            return

        elif text == "📋 Pending Accounts":
            pending_list = [acc for acc in submitted_accounts if acc.get('status') == 'pending']
            if not pending_list:
                bot.send_message(ADMIN_ID, "No pending accounts to review!", reply_markup=admin_panel_keyboard())
                return
            for idx, acc in enumerate(submitted_accounts):
                if acc.get('status') == 'pending':
                    markup = telebot.types.InlineKeyboardMarkup()
                    markup.add(telebot.types.InlineKeyboardButton("Approve", callback_data=f"app_{idx}"), telebot.types.InlineKeyboardButton("Reject", callback_data=f"rej_{idx}"))
                    info = f"User: `{acc['user_id']}`\nTask: `{acc.get('task_name')}`\nUsername: `{acc['username']}`\nPassword: `{acc['password']}`\n2FA: `{acc.get('2fa', 'N/A')}`\nAuth Token: `{acc.get('token', 'N/A')}`"
                    bot.send_message(ADMIN_ID, info, parse_mode="Markdown", reply_markup=markup)
            return

        elif text == "📤 Withdraw Requests":
            pending_wds = [req for req in withdraw_requests if req.get('status', 'pending') == 'pending']
            if not pending_wds:
                bot.send_message(ADMIN_ID, "No pending withdraw requests!", reply_markup=admin_panel_keyboard())
                return
            for idx, req in enumerate(withdraw_requests):
                if req.get('status', 'pending') == 'pending':
                    markup = telebot.types.InlineKeyboardMarkup()
                    markup.row(
                        telebot.types.InlineKeyboardButton("✅ Mark as Paid", callback_data=f"pay_wd_{idx}"),
                        telebot.types.InlineKeyboardButton("❌ Reject & Refund", callback_data=f"rej_wd_{idx}")
                    )
                    info = f"📤 **Withdraw Request ID:** `{idx}`\n• User ID: `{req['user_id']}`\n• Amount: **${req['amount_usd']:.4f}** (~৳{req['amount_bdt']:.2f})\n• Method: **{req['method']}**\n• Details: `{req['details']}`"
                    bot.send_message(ADMIN_ID, info, parse_mode="Markdown", reply_markup=markup)
            return

        elif text == "💰 Change Price":
            markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
            markup.row(telebot.types.KeyboardButton("Change Task 1 Price"), telebot.types.KeyboardButton("Change Task 2 Price"))
            markup.row(telebot.types.KeyboardButton("👑 Admin Panel"))
            bot.send_message(ADMIN_ID, f"💰 **Current Prices:**\n• Task 1: `${SETTINGS['reward_tw_token']:.4f}`\n• Task 2: `${SETTINGS['reward_tw_2fa']:.4f}`\n\nSelect option below to change:", reply_markup=markup, parse_mode="Markdown")
            return

        elif text == "Change Task 1 Price":
            user_steps[ADMIN_ID] = 'set_price_t1'
            bot.send_message(ADMIN_ID, "Send new price for Task 1 in USD ($):", reply_markup=telebot.types.ReplyKeyboardMarkup(resize_keyboard=True).row(telebot.types.KeyboardButton("👑 Admin Panel")))
            return

        elif text == "Change Task 2 Price":
            user_steps[ADMIN_ID] = 'set_price_t2'
            bot.send_message(ADMIN_ID, "Send new price for Task 2 in USD ($):", reply_markup=telebot.types.ReplyKeyboardMarkup(resize_keyboard=True).row(telebot.types.KeyboardButton("👑 Admin Panel")))
            return

        elif text == "✏️ Change Task Names":
            bot.send_message(ADMIN_ID, f"📝 **Task Names:**\n1. `{SETTINGS['task1_name']}`\n2. `{SETTINGS['task2_name']}`", reply_markup=admin_panel_keyboard(), parse_mode="Markdown")
            return

        elif text == "⚙️ Payment Methods":
            bot.send_message(ADMIN_ID, f"⚙️ **Payment Methods Control & Limits:**\n• Minimum Withdraw Limit: ৳{SETTINGS.get('min_withdraw_bdt', 5.0)}", reply_markup=payment_toggle_keyboard(), parse_mode="Markdown")
            return

        elif text == "📢 Broadcast Message":
            user_steps[ADMIN_ID] = 'admin_broadcast_msg'
            bot.send_message(ADMIN_ID, "📢 Send the message you want to broadcast to all users:", reply_markup=telebot.types.ReplyKeyboardMarkup(resize_keyboard=True).row(telebot.types.KeyboardButton("👑 Admin Panel")))
            return

        elif text == "🛠️ Task Control":
            bot.send_message(ADMIN_ID, f"🛠️ **Task Control Status:**\n• Current Report Time: `{SETTINGS.get('task_report_timer_text', 'Every 30 minutes')}`", reply_markup=task_control_keyboard(), parse_mode="Markdown")
            return

    if text == "💰 Balance":
        user_steps.pop(user_id, None)
        u_data = get_user_data(user_id, message.from_user.first_name)
        bal = u_data['balance']
        bdt_bal = bal * SETTINGS['usd_to_bdt']
        pending_wd_usd = sum(req['amount_usd'] for req in withdraw_requests if req['user_id'] == user_id and req.get('status') == 'pending')
        pending_wd_bdt = pending_wd_usd * SETTINGS['usd_to_bdt']
        total_earned_usd = u_data['total_earned']
        total_earned_bdt = total_earned_usd * SETTINGS['usd_to_bdt']
        completed_tasks = u_data['completed_tasks']
        in_review = sum(1 for acc in submitted_accounts if acc.get('user_id') == user_id and acc.get('status') == 'pending')

        balance_text = (
            f"💻 **Your Account Balance:**\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"💰 Balance: {bdt_bal:.2f} BDT (${bal:.3f})\n"
            f"🔄 Pending Withdraw: {pending_wd_bdt:.2f} BDT (${pending_wd_usd:.3f})\n"
            f"💵 Total Income: {total_earned_bdt:.2f} BDT (${total_earned_usd:.3f})\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"✅ Completed Tasks: {completed_tasks}\n"
            f"⌛ In Review: {in_review}"
        )
        bot.send_message(user_id, balance_text, parse_mode="Markdown")
        return

    elif text == "📋 Tasks":
        user_steps.pop(user_id, None)
        if not is_subscribed(user_id):
            bot.send_message(user_id, f"Please join {CHANNEL_USERNAME} first!")
            return
        bot.send_message(user_id, "👇 Please select a task:", reply_markup=tasks_keyboard())
        return

    elif text == "📤 Withdraw":
        user_steps.pop(user_id, None)
        if not SETTINGS.get('withdraw_enabled', True):
            bot.send_message(user_id, "❌ Withdrawal system is currently disabled.")
            return
        u_data = get_user_data(user_id, message.from_user.first_name)
        bal = u_data['balance']
        bdt_amt = bal * SETTINGS['usd_to_bdt']
        min_bdt = SETTINGS['min_withdraw_bdt']

        if bdt_amt < min_bdt:
            bot.send_message(user_id, f"❌ Insufficient balance!\nCurrent Balance: ${bal:.4f} (~৳{bdt_amt:.2f})\nMinimum Withdraw: ৳{min_bdt}")
            return

        markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
        if SETTINGS.get('bkash_enabled', True):
            markup.row(telebot.types.KeyboardButton("💸 Bkash"))
        if SETTINGS.get('nagad_enabled', True):
            markup.row(telebot.types.KeyboardButton("💳 Nagad"))
        if SETTINGS.get('binance_enabled', True):
            markup.row(telebot.types.KeyboardButton("🟡 Binance USDT"))
        markup.row(telebot.types.KeyboardButton("❌ Cancel"))
        user_steps[user_id] = 'awaiting_withdraw_method'
        bot.send_message(user_id, f"💳 Your Balance: ${bal:.4f} (~৳{bdt_amt:.2f})\n\nSelect a payment method to withdraw:", reply_markup=markup)
        return

    elif text == "👤 Profile":
        user_steps.pop(user_id, None)
        u_data = get_user_data(user_id, message.from_user.first_name)
        my_pendings = sum(1 for acc in submitted_accounts if acc.get('user_id') == user_id and acc.get('status') == 'pending')
        profile_text = f"👤 **Profile Info:**\n\n• Name: {u_data.get('name')}\n• User ID: `{user_id}`\n• Completed Tasks: {u_data['completed_tasks']}\n• Pending Accounts: {my_pendings}\n• Balance: ${u_data['balance']:.4f}\n• Total Referrals: {u_data.get('referral_count', 0)}"
        bot.send_message(user_id, profile_text, parse_mode="Markdown")
        return

    elif text == "👥 Referral":
        user_steps.pop(user_id, None)
        if not SETTINGS.get('ref_enabled', True):
            bot.send_message(user_id, "❌ Referral system is currently disabled.")
            return
        u_data = get_user_data(user_id, message.from_user.first_name)
        ref_link = f"https://t.me/{BOT_USERNAME}?start=ref_{user_id}"
        ref_pct = SETTINGS.get('ref_commission_pct', 10.0)
        total_refs = u_data.get('referral_count', 0)
        ref_list = u_data.get('referrals_list', [])
        now_ts = time.time()
        new_24h = sum(1 for r in ref_list if now_ts - r.get('time', 0) <= 86400)
        ref_earned = u_data.get('ref_earned', 0.0)
        ref_msg = (
            f"👥 **Total referrals:** `{total_refs}`\n"
            f"🆕 **New in last 24 hours:** `{new_24h}`\n\n"
            f"💰 **Total Referral Income:** `${ref_earned:.4f}`\n\n"
            f"🔗 **Your referral link:**\n`{ref_link}`\n\n"
            f"ℹ️ You receive **{ref_pct}%** of the earnings of each of your referrals from the tasks they complete."
        )
        bot.send_message(user_id, ref_msg, parse_mode="Markdown")
        return

    elif text == "🏆 Top Leaderboard":
        user_steps.pop(user_id, None)
        if not SETTINGS.get('top_enabled', True):
            bot.send_message(user_id, "❌ Top Leaderboard is currently disabled.")
            return
        now = datetime.datetime.now()
        mode = SETTINGS.get('top_reset_mode', 'daily_10pm')
        if mode == 'custom_minutes':
            rem_secs = int(SETTINGS.get('top_reset_timestamp', time.time()) - time.time())
            if rem_secs < 0:
                rem_secs = 0
            hours = rem_secs // 3600
            minutes = (rem_secs % 3600) // 60
        else:
            target_time = now.replace(hour=22, minute=0, second=0, microsecond=0)
            if mode == 'daily_10pm':
                if now >= target_time:
                    target_time += datetime.timedelta(days=1)
            elif mode == 'sunday_10pm':
                days_ahead = 6 - now.weekday()
                if days_ahead < 0 or (days_ahead == 0 and now >= target_time):
                    days_ahead += 7
                target_time += datetime.timedelta(days=days_ahead)
            rem_secs = int((target_time - now).total_seconds())
            hours = rem_secs // 3600
            minutes = (rem_secs % 3600) // 60

        sorted_u = sorted(users.items(), key=lambda x: x[1].get('completed_tasks', 0), reverse=True)
        top_text = f"🏆 **Top Working Members:**\n⏱️ **Reset in:** `{hours}h {minutes}m`\n\n"
        rw = SETTINGS.get('top_rewards', {})
        for idx, (uid, udata) in enumerate(sorted_u[:10], 1):
            bonus_val = rw.get(idx, 0)
            bonus_str = f" [Bonus: ${bonus_val:.2f}]" if idx <= 5 and bonus_val > 0 else ""
            top_text += f"{idx}. {udata.get('name', 'User')} - **{udata.get('completed_tasks', 0)}** Tasks{bonus_str}\n"
        bot.send_message(user_id, top_text, parse_mode="Markdown")
        return

    elif text == "🎬 Video Tutorial":
        if not videos_list:
            bot.send_message(user_id, "❌ No video tutorial available right now.")
            return
        markup = telebot.types.InlineKeyboardMarkup()
        for idx, v in enumerate(videos_list):
            markup.add(telebot.types.InlineKeyboardButton(f"▶️ {v['title']}", callback_data=f"watch_vid_{idx}"))
        bot.send_message(user_id, "🎬 **Tutorial Videos:**\n\nClick button below:", reply_markup=markup, parse_mode="Markdown")
        return

    elif text.startswith("🐦 ") or SETTINGS['task1_name'] in text:
        report_time = SETTINGS.get('task_report_timer_text', 'Every 30 minutes')
        m1 = bot.send_message(user_id, f"⏳ Report Schedule: {report_time} ⏳\n\n📋 Task: {SETTINGS['task1_name']}\n\n📄 Description: 🔒 REQUIRED!\nYou must use the information provided by the Telegram bot to register.\n\n✍️ Report instruction:\nSubmit 2FA Key and Auth Token to complete.")
        msg = bot.send_message(user_id, "⏳ Ordering email, please wait...")
        mail_obj = create_mailtm_account(SETTINGS['task1_name'])
        if not mail_obj:
            bot.edit_message_text("Server connection error or email limit reached, please try again.", user_id, msg.message_id)
            return
        email, login_user, token, password_gen = mail_obj['email'], mail_obj['username'], mail_obj['token'], mail_obj['password']
        active_mails[user_id] = {'login': login_user, 'email': email, 'token': token}
        user_acc_data[user_id] = {'task_type': 'task1_token', 'login': login_user, 'password': password_gen, 'email': email, 'task_name': SETTINGS['task1_name'], 'msg_ids': []}
        user_steps[user_id] = 'awaiting_email_code_request'
        bot.delete_message(user_id, msg.message_id)
        details_text = f"Login: `{login_user}`\nPassword: `{password_gen}`\nEmail: `{email}`"
        m2 = bot.send_message(user_id, details_text, parse_mode="Markdown")
        markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.row(telebot.types.KeyboardButton("📩 Get code"))
        markup.row(telebot.types.KeyboardButton("❌ Cancel"))
        m3 = bot.send_message(user_id, "👉 Press the button to get the code or cancel the task:", reply_markup=markup)
        user_acc_data[user_id]['msg_ids'] = [m1.message_id, m2.message_id, m3.message_id]
        return

    elif text.startswith("🔥 ") or SETTINGS['task2_name'] in text:
        report_time = SETTINGS.get('task_report_timer_text', 'Every 30 minutes')
        m1 = bot.send_message(user_id, f"⏳ Report Schedule: {report_time} ⏳\n\n📋 Task: {SETTINGS['task2_name']}\n\n📄 Description: 🔒 REQUIRED!\nYou must use the information provided by the Telegram bot to register.\n\n✍️ Report instruction:\nSubmit 2FA Secret Key to get code.")
        msg = bot.send_message(user_id, "⏳ Ordering email, please wait...")
        mail_obj = create_mailtm_account(SETTINGS['task2_name'])
        if not mail_obj:
            bot.edit_message_text("Server connection error or email limit reached, please try again.", user_id, msg.message_id)
            return
        email, login_user, token, password_gen = mail_obj['email'], mail_obj['username'], mail_obj['token'], mail_obj['password']
        active_mails[user_id] = {'login': login_user, 'email': email, 'token': token}
        user_acc_data[user_id] = {'task_type': 'task2_2fa', 'login': login_user, 'password': password_gen, 'email': email, 'task_name': SETTINGS['task2_name'], 'msg_ids': []}
        user_steps[user_id] = 'awaiting_email_code_request'
        bot.delete_message(user_id, msg.message_id)
        details_text = f"Login: `{login_user}`\nPassword: `{password_gen}`\nEmail: `{email}`"
        m2 = bot.send_message(user_id, details_text, parse_mode="Markdown")
        markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.row(telebot.types.KeyboardButton("📩 Get code"))
        markup.row(telebot.types.KeyboardButton("❌ Cancel"))
        m3 = bot.send_message(user_id, "👉 Press the button to get the code or cancel the task:", reply_markup=markup)
        user_acc_data[user_id]['msg_ids'] = [m1.message_id, m2.message_id, m3.message_id]
        return

    elif text in ["Get code", "📩 Get code"]:
        if user_id not in active_mails:
            bot.send_message(user_id, "No active task found!", reply_markup=main_keyboard(user_id))
            return
        msg_wait = bot.send_message(user_id, "Searching for Twitter email, please wait...")
        mail_info = active_mails[user_id]
        otp_code = fetch_twitter_code(mail_info['token'])
        bot.delete_message(user_id, msg_wait.message_id)
        markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.row(telebot.types.KeyboardButton("📩 Get code"))
        markup.row(telebot.types.KeyboardButton("❌ Cancel"))
        if otp_code:
            m_code = bot.send_message(user_id, f"`{otp_code}`", parse_mode="Markdown")
            m_prompt = bot.send_message(user_id, "Tap code above to copy.\n\n🔑 Please enter your 2FA key to get the code:", reply_markup=markup)
            if user_id in user_acc_data and 'msg_ids' in user_acc_data[user_id]:
                user_acc_data[user_id]['msg_ids'].extend([m_code.message_id, m_prompt.message_id])
            user_steps[user_id] = 'awaiting_2fa_key_input'
        else:
            bot.send_message(user_id, "Twitter code not received yet or this code was already used! Please wait 5-10 seconds and click 'Get code' again.", reply_markup=markup)
        return

    step = user_steps.get(user_id)

    if step == 'awaiting_withdraw_method':
        if text in ["💸 Bkash", "💳 Nagad", "🟡 Binance USDT"]:
            clean_method = "Bkash" if "Bkash" in text else ("Nagad" if "Nagad" in text else "Binance")
            user_acc_data[user_id] = {'wd_method': clean_method}
            user_steps[user_id] = 'awaiting_withdraw_amount'
            u_data = get_user_data(user_id)
            bal = u_data['balance']
            bdt_amt = bal * SETTINGS['usd_to_bdt']
            bot.send_message(user_id, f"💳 Your Balance: ${bal:.4f} (~৳{bdt_amt:.2f})\n\n✍️ Please enter the amount you want to withdraw in USD ($):", reply_markup=telebot.types.ReplyKeyboardMarkup(resize_keyboard=True).row(telebot.types.KeyboardButton("❌ Cancel")))
        return

    elif step == 'awaiting_withdraw_amount':
        try:
            amt_usd = float(text.strip())
            u_data = get_user_data(user_id)
            bal = u_data['balance']
            fee_bdt = SETTINGS['withdraw_fee_bdt']
            usd_to_bdt = SETTINGS['usd_to_bdt']
            fee_usd = fee_bdt / usd_to_bdt
            total_deduct_usd = amt_usd + fee_usd
            total_deduct_bdt = total_deduct_usd * usd_to_bdt
            amt_bdt = amt_usd * usd_to_bdt
            min_bdt = SETTINGS['min_withdraw_bdt']

            if amt_usd <= 0:
                bot.send_message(user_id, "❌ Amount must be greater than 0. Enter again:")
                return
            if total_deduct_usd > bal:
                bot.send_message(user_id, f"❌ Insufficient balance including ৳{fee_bdt} fee! You need ${total_deduct_usd:.4f} (~৳{total_deduct_bdt:.2f}), but you have ${bal:.4f}. Enter a valid amount:")
                return
            if amt_bdt < min_bdt:
                bot.send_message(user_id, f"❌ Minimum withdraw is ৳{min_bdt} (~${min_bdt/usd_to_bdt:.4f}). Enter a valid amount:")
                return

            user_acc_data[user_id]['wd_amount_usd'] = amt_usd
            user_acc_data[user_id]['wd_amount_bdt'] = amt_bdt
            user_acc_data[user_id]['wd_total_deduct_usd'] = total_deduct_usd
            method = user_acc_data[user_id]['wd_method']
            user_steps[user_id] = 'awaiting_withdraw_details'

            if method == "Binance":
                bot.send_message(user_id, "✍️ Send your correct **Binance UID** (must be exactly 9 digits, e.g. `123456789`):", reply_markup=telebot.types.ReplyKeyboardMarkup(resize_keyboard=True).row(telebot.types.KeyboardButton("❌ Cancel")))
            else:
                bot.send_message(user_id, f"✍️ Send your correct **{method}** account number (11 digits, e.g. `017xxxxxxxx`):", reply_markup=telebot.types.ReplyKeyboardMarkup(resize_keyboard=True).row(telebot.types.KeyboardButton("❌ Cancel")))
        except ValueError:
            bot.send_message(user_id, "❌ Invalid number format! Please enter a valid number in USD (e.g. 5.0):")
        return

    elif step == 'awaiting_withdraw_details':
        method = user_acc_data.get(user_id, {}).get('wd_method', 'Bkash')
        details = text.strip()
        if method in ["Bkash", "Nagad"]:
            if not re.match(r'^01[0-9]{9}$', details):
                bot.send_message(user_id, f"❌ Invalid number! Please enter a valid 11-digit {method} number (e.g. 017xxxxxxxx):")
                return
        elif method == "Binance":
            if not re.match(r'^\d{9}$', details):
                bot.send_message(user_id, "❌ Invalid Binance UID! Please enter exactly **9 digits** numeric Binance UID (e.g. `123456789`):")
                return

        amt_usd = user_acc_data[user_id]['wd_amount_usd']
        amt_bdt = user_acc_data[user_id]['wd_amount_bdt']
        total_deduct_usd = user_acc_data[user_id]['wd_total_deduct_usd']

        u_data = get_user_data(user_id)
        u_data['balance'] -= total_deduct_usd 
        req_obj = {'user_id': user_id, 'amount_usd': amt_usd, 'amount_bdt': amt_bdt, 'method': method, 'details': details, 'status': 'pending'}
        withdraw_requests.append(req_obj)
        user_steps.pop(user_id, None)
        user_acc_data.pop(user_id, None)

        bot.send_message(user_id, f"✅ Withdraw request submitted successfully!\nAmount: ৳{amt_bdt:.2f} (~${amt_usd:.4f}) + ৳{SETTINGS['withdraw_fee_bdt']} fee ({method})", reply_markup=main_keyboard(user_id))
        try:
            bot.send_message(ADMIN_ID, f"📤 **New Withdraw Request!**\nUser ID: `{user_id}`\nAmount: `${amt_usd:.4f}` (~৳{amt_bdt:.2f})\nMethod: **{method}**\nDetails: `{details}`", parse_mode="Markdown")
        except Exception:
            pass
        return

    elif step == 'awaiting_2fa_key_input':
        clean_key = text.replace(" ", "").upper()
        if len(clean_key) != 16:
            bot.send_message(user_id, f"❌ Error! Twitter 2FA Secret Key must be exactly **16 characters**. You entered {len(clean_key)} characters. Try again:")
            return
        
        is_duplicate = False
        for prev_acc in submitted_accounts + rejected_accounts_db:
            if prev_acc.get('2fa', '').upper() == clean_key:
                is_duplicate = True
                break

        if is_duplicate:
            rejected_entry = {
                'task_name': user_acc_data.get(user_id, {}).get('task_name', 'Task'),
                'username': user_acc_data.get(user_id, {}).get('login', 'duplicate_user'),
                'password': user_acc_data.get(user_id, {}).get('password', 'N/A'),
                '2fa': clean_key,
                'token': 'N/A',
                'user_id': user_id,
                'status': 'rejected',
                'time': time.strftime("%Y-%m-%d %H:%M:%S")
            }
            rejected_accounts_db.append(rejected_entry)
            clear_user_chat_session(user_id, {user_id: user_acc_data.get(user_id, {}).get('msg_ids', [])})
            bot.send_message(user_id, "❌ This 2FA Secret Key has already been submitted! Account automatically rejected.", reply_markup=main_keyboard(user_id))
            active_mails.pop(user_id, None)
            user_steps.pop(user_id, None)
            user_acc_data.pop(user_id, None)
            return

        try:
            totp = pyotp.TOTP(clean_key)
            current_otp = totp.now()
        except Exception:
            bot.send_message(user_id, "❌ Invalid 2FA Key format! Please send a valid 16-character Secret Key:")
            return

        user_acc_data[user_id]['2fa'] = clean_key
        task_type = user_acc_data[user_id]['task_type']

        if task_type == 'task1_token':
            user_steps[user_id] = 'awaiting_auth_token_input'
            markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
            markup.row(telebot.types.KeyboardButton("❌ Cancel"))
            m_code = bot.send_message(user_id, f"`{current_otp}`", parse_mode="Markdown")
            m_prompt = bot.send_message(user_id, "📋 Your one-time code:\n\n👆 Tap the code to copy\n\nPlease send the account auth_token / cookies:", reply_markup=markup)
            if 'msg_ids' in user_acc_data[user_id]:
                user_acc_data[user_id]['msg_ids'].extend([m_code.message_id, m_prompt.message_id])

        elif task_type == 'task2_2fa':
            user_steps[user_id] = 'awaiting_final_confirmation'
            markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
            markup.row(telebot.types.KeyboardButton("✅ Confirm"), telebot.types.KeyboardButton("❌ Cancel"))
            m_code = bot.send_message(user_id, f"`{current_otp}`", parse_mode="Markdown")
            m_prompt = bot.send_message(user_id, "📋 Your one-time code:\n\n👆 Tap the code to copy\n\nPlease press **✅ Confirm** or **❌ Cancel**:", reply_markup=markup, parse_mode="Markdown")
            if 'msg_ids' in user_acc_data[user_id]:
                user_acc_data[user_id]['msg_ids'].extend([m_code.message_id, m_prompt.message_id])
        return

    elif step == 'awaiting_auth_token_input':
        extracted_token = extract_auth_token(text)

        is_duplicate = False
        for prev_acc in submitted_accounts + rejected_accounts_db:
            if prev_acc.get('token') and prev_acc.get('token') != 'N/A' and prev_acc.get('token') == extracted_token:
                is_duplicate = True
                break

        if is_duplicate:
            acc_data = user_acc_data.get(user_id, {})
            rejected_entry = {
                'task_name': acc_data.get('task_name', 'Task'),
                'username': acc_data.get('login', 'duplicate_user'),
                'password': acc_data.get('password', 'N/A'),
                '2fa': acc_data.get('2fa', 'N/A'),
                'token': extracted_token,
                'user_id': user_id,
                'status': 'rejected',
                'time': time.strftime("%Y-%m-%d %H:%M:%S")
            }
            rejected_accounts_db.append(rejected_entry)
            clear_user_chat_session(user_id, {user_id: acc_data.get('msg_ids', [])})
            bot.send_message(user_id, "❌ This Auth Token has already been submitted! Account automatically rejected.", reply_markup=main_keyboard(user_id))
            active_mails.pop(user_id, None)
            user_steps.pop(user_id, None)
            user_acc_data.pop(user_id, None)
            return

        user_acc_data[user_id]['token'] = extracted_token
        acc_data = user_acc_data.get(user_id, {})
        acc_entry = {
            'task_name': acc_data.get('task_name'),
            'username': acc_data.get('login'),
            'password': acc_data.get('password'),
            '2fa': acc_data.get('2fa', 'N/A'),
            'token': acc_data.get('token', 'N/A'),
            'user_id': user_id,
            'status': 'pending',
            'time': time.strftime("%Y-%m-%d %H:%M:%S")
        }
        submitted_accounts.append(acc_entry)
        markup = telebot.types.InlineKeyboardMarkup()
        acc_index = len(submitted_accounts) - 1
        markup.add(telebot.types.InlineKeyboardButton("Approve", callback_data=f"app_{acc_index}"), telebot.types.InlineKeyboardButton("Reject", callback_data=f"rej_{acc_index}"))

        admin_alert = f"New Account Pending Approval!\n\nUser: `{user_id}`\nTask: `{acc_entry['task_name']}`\nUsername: `{acc_entry['username']}`\nPassword: `{acc_entry['password']}`\n2FA: `{acc_entry['2fa']}`\nAuth Token: `{acc_entry['token']}`"
        try:
            bot.send_message(ADMIN_ID, admin_alert, reply_markup=markup, parse_mode="Markdown")
        except Exception:
            pass

        clear_user_chat_session(user_id, {user_id: acc_data.get('msg_ids', [])})
        bot.send_message(user_id, "✅ Account submitted successfully! Waiting for admin approval.", reply_markup=main_keyboard(user_id))
        active_mails.pop(user_id, None)
        user_steps.pop(user_id, None)
        user_acc_data.pop(user_id, None)
        return

    elif step == 'awaiting_final_confirmation':
        if text == "✅ Confirm":
            acc_data = user_acc_data.get(user_id, {})
            acc_entry = {
                'task_name': acc_data.get('task_name'),
                'username': acc_data.get('login'),
                'password': acc_data.get('password'),
                '2fa': acc_data.get('2fa', 'N/A'),
                'token': acc_data.get('token', 'N/A'),
                'user_id': user_id,
                'status': 'pending',
                'time': time.strftime("%Y-%m-%d %H:%M:%S")
            }
            submitted_accounts.append(acc_entry)
            markup = telebot.types.InlineKeyboardMarkup()
            acc_index = len(submitted_accounts) - 1
            markup.add(telebot.types.InlineKeyboardButton("Approve", callback_data=f"app_{acc_index}"), telebot.types.InlineKeyboardButton("Reject", callback_data=f"rej_{acc_index}"))

            admin_alert = f"New Account Pending Approval!\n\nUser: `{user_id}`\nTask: `{acc_entry['task_name']}`\nUsername: `{acc_entry['username']}`\nPassword: `{acc_entry['password']}`\n2FA: `{acc_entry['2fa']}`\nAuth Token: `{acc_entry['token']}`"
            try:
                bot.send_message(ADMIN_ID, admin_alert, reply_markup=markup, parse_mode="Markdown")
            except Exception:
                pass

            clear_user_chat_session(user_id, {user_id: acc_data.get('msg_ids', [])})
            bot.send_message(user_id, "✅ Account submitted successfully! Waiting for admin approval.", reply_markup=main_keyboard(user_id))
            active_mails.pop(user_id, None)
            user_steps.pop(user_id, None)
            user_acc_data.pop(user_id, None)
            return
        else:
            markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
            markup.row(telebot.types.KeyboardButton("✅ Confirm"), telebot.types.KeyboardButton("❌ Cancel"))
            bot.send_message(user_id, "Please press **✅ Confirm** or **❌ Cancel**", reply_markup=markup, parse_mode="Markdown")
            return

@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    global submitted_accounts, rejected_accounts_db, withdraw_requests, videos_list, downloaded_status, blocked_users, rejected_history_db
    data = call.data
    user_id = call.from_user.id

    if user_id != ADMIN_ID:
        return

    if data.startswith("adm_block_"):
        target_uid = int(data.replace("adm_block_", ""))
        blocked_users.add(target_uid)
        bot.answer_callback_query(call.id, f"User {target_uid} blocked!")
        try:
            bot.edit_message_text(call.message.text + "\n\n**[Status: BLOCKED 🔴]**", call.message.chat.id, call.message.message_id, parse_mode="Markdown")
        except Exception:
            pass

    elif data.startswith("adm_unblock_"):
        target_uid = int(data.replace("adm_unblock_", ""))
        blocked_users.discard(target_uid)
        bot.answer_callback_query(call.id, f"User {target_uid} unblocked!")
        try:
            bot.edit_message_text(call.message.text + "\n\n**[Status: ACTIVE 🟢]**", call.message.chat.id, call.message.message_id, parse_mode="Markdown")
        except Exception:
            pass

    elif data.startswith("adm_edit_bal_"):
        target_uid = int(data.replace("adm_edit_bal_", ""))
        user_steps[ADMIN_ID] = f"adm_set_bal_{target_uid}"
        bot.answer_callback_query(call.id)
        bot.send_message(ADMIN_ID, f"✍️ Send new balance in USD ($) for user (`{target_uid}`):", reply_markup=telebot.types.ReplyKeyboardMarkup(resize_keyboard=True).row(telebot.types.KeyboardButton("👑 Admin Panel")))

    elif data == "conf_del_t1":
        before_count = len(submitted_accounts)
        submitted_accounts[:] = [acc for acc in submitted_accounts if acc.get('task_name') != SETTINGS['task1_name']]
        deleted_count = before_count - len(submitted_accounts)
        downloaded_status['task1'] = False
        bot.answer_callback_query(call.id, f"Deleted {deleted_count} accounts!")
        try:
            bot.edit_message_text(f"🗑️ Successfully deleted `{deleted_count}` Task 1 accounts and reset status.", call.message.chat.id, call.message.message_id, parse_mode="Markdown")
        except Exception:
            pass

    elif data == "conf_del_t2":
        before_count = len(submitted_accounts)
        submitted_accounts[:] = [acc for acc in submitted_accounts if acc.get('task_name') != SETTINGS['task2_name']]
        deleted_count = before_count - len(submitted_accounts)
        downloaded_status['task2'] = False
        bot.answer_callback_query(call.id, f"Deleted {deleted_count} accounts!")
        try:
            bot.edit_message_text(f"🗑️ Successfully deleted `{deleted_count}` Task 2 accounts and reset status.", call.message.chat.id, call.message.message_id, parse_mode="Markdown")
        except Exception:
            pass

    elif data == "cancel_del":
        bot.answer_callback_query(call.id, "Cancelled!")
        try:
            bot.edit_message_text("❌ Account deletion process cancelled.", call.message.chat.id, call.message.message_id)
        except Exception:
            pass

    elif data.startswith("app_uid_"):
        target_uid = int(data.split("_")[2])
        count = 0
        for acc in submitted_accounts:
            if acc.get('user_id') == target_uid and acc.get('status') == 'pending':
                if approve_single_account(acc):
                    count += 1
        bot.answer_callback_query(call.id, f"{count} accounts approved!")
        try:
            bot.edit_message_text(f"✅ Approved all pending accounts for UID: `{target_uid}` (Total: {count})", call.message.chat.id, call.message.message_id, parse_mode="Markdown")
        except Exception:
            pass

    elif data.startswith("rej_uid_"):
        target_uid = int(data.split("_")[2])
        count = 0
        for acc in submitted_accounts:
            if acc.get('user_id') == target_uid and acc.get('status') == 'pending':
                if reject_single_account(acc):
                    count += 1
        bot.answer_callback_query(call.id, f"{count} accounts rejected!")
        try:
            bot.edit_message_text(f"❌ Rejected all pending accounts for UID: `{target_uid}` (Total: {count})", call.message.chat.id, call.message.message_id, parse_mode="Markdown")
        except Exception:
            pass

    elif data.startswith("app_"):
        idx = int(data.split("_")[1])
        if idx < len(submitted_accounts):
            acc = submitted_accounts[idx]
            if acc.get('status') == 'approved':
                bot.answer_callback_query(call.id, "Already approved!")
                return
            approve_single_account(acc)
            bot.answer_callback_query(call.id, "Approved!")
            try:
                bot.edit_message_text(call.message.text + "\n\n**[Status: APPROVED]**", call.message.chat.id, call.message.message_id, parse_mode="Markdown")
            except Exception:
                pass

    elif data.startswith("rej_"):
        idx = int(data.split("_")[1])
        if idx < len(submitted_accounts):
            acc = submitted_accounts[idx]
            reject_single_account(acc)
            bot.answer_callback_query(call.id, "Rejected!")
            try:
                bot.edit_message_text(call.message.text + "\n\n**[Status: REJECTED]**", call.message.chat.id, call.message.message_id, parse_mode="Markdown")
            except Exception:
                pass

    elif data.startswith("pay_wd_"):
        idx = int(data.split("_")[2])
        if idx < len(withdraw_requests):
            req = withdraw_requests[idx]
            if req.get('status') == 'paid':
                bot.answer_callback_query(call.id, "Already paid!")
                return
            
            user_steps[ADMIN_ID] = f"admin_awaiting_payment_screenshot_{idx}"
            bot.answer_callback_query(call.id, "Send payment screenshot:")
            bot.send_message(ADMIN_ID, f"📤 Send a **screenshot (Photo)** to confirm payment for request ID `{idx}`:", parse_mode="Markdown")
            try:
                bot.edit_message_text(call.message.text + "\n\n**[Awaiting Payment Screenshot 📸]**", call.message.chat.id, call.message.message_id, parse_mode="Markdown")
            except Exception:
                pass

    elif data.startswith("rej_wd_"):
        idx = int(data.split("_")[2])
        if idx < len(withdraw_requests):
            req = withdraw_requests[idx]
            if req.get('status') in ['rejected', 'refunded']:
                bot.answer_callback_query(call.id, "Already rejected/refunded!")
                return
            req['status'] = 'refunded'
            target_uid = req['user_id']
            refund_amt = req['amount_usd'] + (SETTINGS['withdraw_fee_bdt'] / SETTINGS['usd_to_bdt'])
            if target_uid in users:
                users[target_uid]['balance'] += refund_amt
            try:
                bot.send_message(target_uid, f"❌ Your withdrawal request was rejected and ${refund_amt:.4f} (including fee) has been refunded to your balance.")
            except Exception:
                pass
            bot.answer_callback_query(call.id, "Rejected & Refunded!")
            try:
                bot.edit_message_text(call.message.text + "\n\n**[Status: REJECTED & REFUNDED ❌]**", call.message.chat.id, call.message.message_id, parse_mode="Markdown")
            except Exception:
                pass

if __name__ == '__main__':
    print("Bot is running...")
    # ফ্লাস্ক সার্ভার ব্যাকগ্রাউন্ড থ্রেডে চলবে
    web_thread = threading.Thread(target=run_web)
    web_thread.daemon = True
    web_thread.start()
    
    # টেলিগ্রাম বট পলিং শুরু করা
    try:
        bot.infinity_polling(skip_pending=True)
    except Exception as e:
        print(f"Polling error: {e}")
