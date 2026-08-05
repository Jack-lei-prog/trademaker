# -*- coding: utf-8 -*-
"""
WSGI 入口 — 生产环境使用 gunicorn wsgi:app
启动命令: gunicorn wsgi:app --bind 0.0.0.0:$PORT --workers=2 --timeout=120
"""
from app import app

if __name__ == "__main__":
    import os
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
