from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def home():
    return "✅ Bot is running!", 200

def run():
    # Flask буде працювати на порту Render/Replit
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    # Запуск Flask у фоновому потоці, щоб бот не падав
    t = Thread(target=run)
    t.start()
