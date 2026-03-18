import os
import json
import threading
import requests
from flask import Flask, render_template, request
# Đảm bảo đã cài đặt: pip install zalo-bot flask requests
from zalo_bot import Update
from zalo_bot.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters

app = Flask(__name__)
CONFIG_FILE = 'config.json'

def get_config():
    if not os.path.exists(CONFIG_FILE):
        # Ưu tiên lấy từ môi trường Render nếu file chưa có
        return {
            "gemini_key": os.environ.get("GEMINI_KEY", ""),
            "zalo_token": os.environ.get("ZALO_TOKEN", "")
        }
    with open(CONFIG_FILE, 'r') as f:
        return json.load(f)

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
    return "Đã lưu! Hãy Restart Service để áp dụng.", 200

def ask_gemini(prompt, api_key):
    # Dùng bản 1.5 Flash cho nhanh và ổn định
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    try:
        res = requests.post(url, json=payload, timeout=10)
        res_json = res.json()
        return res_json['candidates'][0]['content']['parts'][0]['text']
    except Exception as e:
        print(f"Lỗi Gemini: {e}")
        return "AI đang bận hoặc Key lỗi rồi bro!"

async def handle_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conf = get_config()
    if conf['gemini_key'] and update.message.text:
        reply = ask_gemini(update.message.text, conf['gemini_key'])
        await update.message.reply_text(reply)

def run_zalo_bot():
    conf = get_config()
    if conf['zalo_token']:
        try:
            # Khởi tạo bot app
            bot_app = ApplicationBuilder().token(conf['zalo_token']).build()
            bot_app.add_handler(MessageHandler(filters.TEXT, handle_msg))
            print("🤖 Bot Zalo đang khởi động...")
            bot_app.run_polling()
        except Exception as e:
            print(f"Lỗi khởi động Bot: {e}")

if __name__ == "__main__":
    # Khởi chạy luồng Bot
    bot_thread = threading.Thread(target=run_zalo_bot, daemon=True)
    bot_thread.start()
    
    # Khởi chạy Flask App
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
