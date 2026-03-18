import os
import json
import requests
from flask import Flask, render_template, request, redirect, jsonify

app = Flask(__name__)

# Cấu hình mặc định (Lấy từ ảnh của bạn)
config = {
    "app_id": "1190675959822536262",
    "secret_key": "gUwSpJrBF5bSRNB8C1U3",
    "gemini_key": "",
    "zalo_access_token": "",
    "zalo_refresh_token": ""
}

# Giao diện Admin để điền Key
@app.route('/')
def index():
    return render_template('index.html', config=config)

@app.route('/save', methods=['POST'])
def save():
    global config
    config['gemini_key'] = request.form.get('gemini_key')
    config['zalo_access_token'] = request.form.get('zalo_access_token')
    config['zalo_refresh_token'] = request.form.get('zalo_refresh_token')
    return redirect('/')

# Webhook Zalo
@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    if data and "message" in data:
        uid = data["sender"]["id"]
        text = data["message"].get("text", "")
        
        # Gọi Gemini xử lý (Nếu đã điền Key)
        reply = get_gemini_response(text) if config['gemini_key'] else f"Bot nhận được: {text}"
        
        # Gửi tin nhắn phản hồi
        send_zalo(uid, reply)
    return "OK", 200

def get_gemini_response(prompt):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={config['gemini_key']}"
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    try:
        res = requests.post(url, json=payload)
        return res.json()['candidates'][0]['content']['parts'][0]['text']
    except:
        return "Lỗi kết nối Gemini rồi bro ơi!"

def send_zalo(uid, text):
    headers = {"access_token": config['zalo_access_token']}
    payload = {"recipient": {"user_id": uid}, "message": {"text": text}}
    requests.post("https://openapi.zalo.me/v2.0/oa/message", json=payload, headers=headers)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
