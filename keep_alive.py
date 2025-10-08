from flask import Flask, jsonify

app = Flask(__name__)

# Тут бот зберігає всі ключі
keys_data = []

@app.route('/')
def home():
    return "✅ NexusVision API running"

@app.route('/keys')
def get_keys():
    return jsonify(keys_data)

def add_key(key, active, days):
    keys_data.append({
        "key": key,
        "active": active,
        "days": days
    })

def keep_alive():
    from threading import Thread
    t = Thread(target=lambda: app.run(host='0.0.0.0', port=8080))
    t.start()
