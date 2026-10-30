from flask import Flask, request, jsonify,render_template
import sqlite3
from classifier import HiMLIC
import threading
import time
import random
app = Flask(__name__)
model = HiMLIC(mode="Light")

def log_to_db(features, l1, l2):
    conn = sqlite3.connect('hi_mlic.db')
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO intrusion_logs (feature_vector, layer1_result, layer2_result, mode) VALUES (?, ?, ?, ?)",
        (str(features), l1, l2, model.mode)
    )
    conn.commit()
    conn.close()
import os

# Get the directory where app.py is located
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(BASE_DIR, "hi_mlic.db")

def get_db_connection():
    conn = sqlite3.connect('hi_mlic.db')
    conn.row_factory = sqlite3.Row
    return conn


ATTACK_TYPES = ["DDoS", "SQL Injection", "Brute Force", "Port Scan", "XSS"]
DEVICES = ["IoT-Sensor-A1", "Enterprise-Srv-04", "Gateway-Node"]

def simulate_traffic():
    """Generates random traffic every 2-5 seconds."""
    while True:
        time.sleep(random.uniform(2, 5))
        
        # Layer 1 Logic: 70% Benign, 30% Malicious
        is_malicious = random.choices([True, False], weights=[30, 70])[0]
        l1_result = "Malicious" if is_malicious else "Benign"
        
        # Layer 2 Logic: Only triggered if Layer 1 is Malicious
        l2_result = random.choice(ATTACK_TYPES) if is_malicious else "N/A"
        
        # Random Metadata
        mode = random.choice(["Light", "Full"])
        features = [round(random.uniform(0, 1), 4) for _ in range(4)]
        
        # Log to Database
        try:
            conn = sqlite3.connect('hi_mlic.db')
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO intrusion_logs (feature_vector, layer1_result, layer2_result, mode) VALUES (?, ?, ?, ?)",
                (str(features), l1_result, l2_result, mode)
            )
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Simulation Error: {e}")

# Start simulation in a background thread
threading.Thread(target=simulate_traffic, daemon=True).start()

# --- ROUTES ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/stats')
def stats():
    conn = sqlite3.connect('hi_mlic.db')
    conn.row_factory = sqlite3.Row
    
    # Summary
    total = conn.execute('SELECT COUNT(*) FROM intrusion_logs').fetchone()[0]
    malicious = conn.execute('SELECT COUNT(*) FROM intrusion_logs WHERE layer1_result = "Malicious"').fetchone()[0]
    
    # Chart: Attack Distribution
    types = conn.execute('SELECT layer2_result, COUNT(*) as count FROM intrusion_logs WHERE layer2_result != "N/A" GROUP BY layer2_result').fetchall()
    
    # Recent Logs
    recent = conn.execute('SELECT * FROM intrusion_logs ORDER BY id DESC LIMIT 10').fetchall()
    
    # History for Trend (Last 20)
    history = conn.execute('SELECT layer1_result FROM intrusion_logs ORDER BY id DESC LIMIT 20').fetchall()
    
    conn.close()
    
    return jsonify({
        "summary": {
            "total": total,
            "malicious": malicious,
            "benign": total - malicious,
            "threat_percent": round((malicious/total)*100, 1) if total > 0 else 0
        },
        "chart_data": {row['layer2_result']: row['count'] for row in types},
        "history": [1 if h['layer1_result'] == "Malicious" else 0 for h in reversed(history)],
        "recent_logs": [dict(row) for row in recent]
    })

@app.route('/detect', methods=['POST'])
def detect():
    data = request.json.get('features') # Expecting a list of floats
    
    if not data:
        return jsonify({"error": "No features provided"}), 400

    # Execute Hierarchical Classification
    l1_status, l2_type = model.predict(data)
    
    # Persistent Logging
    log_to_db(data, l1_status, l2_type)
    
    return jsonify({
        "status": "success",
        "layer_1": l1_status,
        "layer_2_attack_type": l2_type,
        "deployment_mode": model.mode
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000)