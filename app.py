import os
import json
import threading
import requests
from flask import Flask, render_template, request, redirect
from zalo_bot import Update
from zalo_bot.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters

app = Flask(__name__)
CONFIG_FILE = 'config.json'

# Hàm đọc/ghi cấu hình
def get_config():
    if not os.path.exists(CONFIG_FILE):
        return {"gemini_key": "", "zalo_token": ""}
    with open(CONFIG_FILE, 'r') as f:
        return json.load(f)

def save_config(data):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(data, f)

# --- PHẦN 1: GIAO DIỆN WEB (FLASK) ---
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
    return "Đã lưu! Hãy Restart Service trên Render để áp dụng key mới.", 200

# --- PHẦN 2: LOGIC BOT ZALO ---
def ask_gemini(prompt, api_key):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    try:
        res = requests.post(url, json=payload, timeout=10)
        return res.json()['candidates'][0]['content']['parts'][0]['text']
    except:
        return "AI đang bận hoặc Key lỗi rồi bro!"

async def handle_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conf = get_config()
    if conf['gemini_key'] and conf['zalo_token']:
        reply = ask_gemini(update.message.text, conf['gemini_key'])
        await update.message.reply_text(reply)

def run_zalo_bot():
    conf = get_config()
    if conf['zalo_token']:
        try:
            bot_app = ApplicationBuilder().token(conf['zalo_token']).build()
            bot_app.add_handler(MessageHandler(filters.TEXT, handle_msg))
            print("🤖 Zalo Bot đang quét tin nhắn...")
            bot_app.run_polling()
        except Exception as e:
            print(f"Lỗi Bot: {e}")

# --- CHẠY SONG SONG ---
if __name__ == "__main__":
    # Chạy Bot Zalo trong một luồng riêng
    threading.Thread(target=run_zalo_bot, daemon=True).start()
    
    # Chạy Web Dashboard
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
