import sys
import os
import subprocess

# Ép Python tìm trong thư mục site-packages của User và môi trường ảo Render
try:
    user_site = subprocess.check_output([sys.executable, "-m", "site", "--user-site"]).decode('utf-8').strip()
    sys.path.append(user_site)
except:
    pass

sys.path.append("/opt/render/project/src/.venv/lib/python3.10/site-packages")

import json
import threading
import requests
from flask import Flask, render_template, request

# Import Zalo Bot sau khi đã xử lý Path
from zalo_bot import Update
from zalo_bot.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters

app = Flask(__name__)
CONFIG_FILE = 'config.json'

def get_config():
    if not os.path.exists(CONFIG_FILE):
        return {
            "gemini_key": os.environ.get("GEMINI_KEY", ""),
            "zalo_token": os.environ.get("ZALO_TOKEN", "")
        }
    with open(CONFIG_FILE, 'r') as f:
        try:
            return json.load(f)
        except:
            return {"gemini_key": "", "zalo_token": ""}

def save_config(data):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(data, f)

@app.route('/')
def index():
    return render_template('index.html', config=get_config())

@app.route('/save', methods=['POST'])
def save():
    config = {
        "gemini_key": request.form.get('gemini_key'),
        "zalo_token": request.form.get('zalo_token')
    }
    save_config(config)
    return "✅ Đã lưu! Hãy Restart Service để áp dụng Key mới.", 200

def ask_gemini(prompt, api_key):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    try:
        res = requests.post(url, json=payload, timeout=15)
        return res.json()['candidates'][0]['content']['parts'][0]['text']
    except Exception as e:
        print(f"Lỗi Gemini: {e}")
        return "AI đang bận, thử lại sau nhé bro!"

async def handle_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conf = get_config()
    if conf['gemini_key'] and update.message.text:
        print(f"📩 Tin nhắn: {update.message.text}")
        reply = ask_gemini(update.message.text, conf['gemini_key'])
        await update.message.reply_text(reply)

def run_zalo_bot():
    conf = get_config()
    if conf['zalo_token']:
        try:
            bot_app = ApplicationBuilder().token(conf['zalo_token']).build()
            bot_app.add_handler(MessageHandler(filters.TEXT, handle_msg))
            print("🤖 Zalo Bot đang khởi động...")
            bot_app.run_polling()
        except Exception as e:
            print(f"Lỗi Bot: {e}")

if __name__ == "__main__":
    # Luồng Bot chạy ngầm
    threading.Thread(target=run_zalo_bot, daemon=True).start()
    
    # Dashboard Web
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
