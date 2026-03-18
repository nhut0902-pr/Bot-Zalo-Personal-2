import sys
import os
import subprocess

# Ép Python tìm trong thư mục site-packages của User
user_site = subprocess.check_output([sys.executable, "-m", "site", "--user-site"]).decode('utf-8').strip()
sys.path.append(user_site)

# Thêm dự phòng cho môi trường ảo Render
sys.path.append("/opt/render/project/src/.venv/lib/python3.10/site-packages")

import json
import threading
import requests
from flask import Flask, render_template, request

# Bây giờ mới import Zalo Bot
from zalo_bot import Update
from zalo_bot.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters

# ... (các phần code còn lại giữ nguyên)
