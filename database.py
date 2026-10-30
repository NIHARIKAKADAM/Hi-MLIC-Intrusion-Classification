import sqlite3

def init_db():
    conn = sqlite3.connect('hi_mlic.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS intrusion_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            feature_vector TEXT,
            layer1_result TEXT,
            layer2_result TEXT,
            mode TEXT
        )
    ''')
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()