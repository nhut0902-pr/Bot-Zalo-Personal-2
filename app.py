import sys
import os

# Bước quan trọng: Ép Python tìm thư viện trong thư mục site-packages của Render
venv_path = os.path.join(os.getcwd(), ".venv/lib/python3.10/site-packages")
if os.path.exists(venv_path):
    sys.path.append(venv_path)

import json
import threading
import requests
from flask import Flask, render_template, request

# Import thư viện zalo-bot sau khi đã cấu hình path
try:
    from zalo_bot import Update
    from zalo_bot.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters
except ImportError:
    print("⚠️ Cảnh báo: Không tìm thấy thư viện zalo-bot trong path!")

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
    return "✅ Đã lưu thành công! Hãy nhấn 'Manual Deploy -> Clear Build Cache' trên Render để bot nhận key mới.", 200

def ask_gemini(prompt, api_key):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    try:
        res = requests.post(url, json=payload, timeout=15)
        res_data = res.json()
        return res_data['candidates'][0]['content']['parts'][0]['text']
    except Exception as e:
        print(f"❌ Lỗi Gemini: {e}")
        return "Bot đang bận một chút, bro thử lại sau nhé!"

async def handle_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conf = get_config()
    user_msg = update.message.text
    
    if conf['gemini_key'] and user_msg:
        print(f"📩 Tin nhắn đến: {user_msg}")
        reply = ask_gemini(user_msg, conf['gemini_key'])
        await update.message.reply_text(reply)

def run_zalo_bot():
    conf = get_config()
    if not conf['zalo_token'] or conf['zalo_token'] == "":
        print("ℹ️ Chưa có Zalo Token. Hãy nhập trên Dashboard Web.")
        return

    try:
        bot_app = ApplicationBuilder().token(conf['zalo_token']).build()
        bot_app.add_handler(MessageHandler(filters.TEXT, handle_msg))
        print("🤖 Zalo Bot đã sẵn sàng và đang quét tin nhắn...")
        bot_app.run_polling()
    except Exception as e:
        print(f"❌ Lỗi khởi động Bot: {e}")

if __name__ == "__main__":
    # Chạy Bot trong luồng riêng để không làm treo Web Dashboard
    bot_thread = threading.Thread(target=run_zalo_bot, daemon=True)
    bot_thread.start()
    
    # Chạy Flask App (Web Dashboard)
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
