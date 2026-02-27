import sqlite3
import hashlib
import pandas as pd
import matplotlib.pyplot as plt
import os

DB_FILE = "/tmp/sukoon_e_zehn.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS health_logs (username TEXT, date TEXT, stress INTEGER, mood INTEGER, sleep REAL)')
    c.execute('CREATE TABLE IF NOT EXISTS appointments (username TEXT, doctor TEXT, provider TEXT, date_time TEXT, status TEXT)')
    conn.commit()
    conn.close()

def hash_password(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def signup_user(username, password):
    if not username or not password: return "❌ Fields cannot be empty"
    conn = sqlite3.connect(DB_FILE); c = conn.cursor()
    try:
        c.execute("INSERT INTO users VALUES (?, ?)", (username, hash_password(password)))
        conn.commit()
        return "✅ Account created successfully! Please login."
    except sqlite3.IntegrityError: return "❌ Username already exists."
    finally: conn.close()

def login_user(username, password):
    if not os.path.exists(DB_FILE): init_db()
    conn = sqlite3.connect(DB_FILE); c = conn.cursor()
    c.execute("SELECT password FROM users WHERE username=?", (username,))
    res = c.fetchone()
    conn.close()
    return res and res[0] == hash_password(password)

def save_and_plot(user, stress, mood, sleep):
    if not user: return None, "❌ Please login first"
    
    # Prevents flickering and overlapping plots
    plt.close('all') 
    
    conn = sqlite3.connect(DB_FILE); c = conn.cursor()
    date = pd.Timestamp.now().strftime("%m-%d %H:%M")
    c.execute("INSERT INTO health_logs VALUES (?, ?, ?, ?, ?)", (user, date, stress, mood, sleep))
    conn.commit()
    df = pd.read_sql_query(f"SELECT date, stress, mood, sleep FROM health_logs WHERE username='{user}'", conn)
    conn.close()
    
    fig, ax1 = plt.subplots(figsize=(8, 5))
    ax1.plot(df['date'], df['mood'], label="Mood", marker='o', color='#4CAF50', linewidth=2)
    ax1.plot(df['date'], df['stress'], label="Stress", marker='x', color='#F44336', linewidth=2)
    ax1.set_ylabel("Rating (1-10)")
    ax1.set_ylim(0, 11)
    
    ax2 = ax1.twinx()
    ax2.bar(df['date'], df['sleep'], alpha=0.3, color='#2196F3', label="Sleep")
    ax2.set_ylabel("Hours")
    ax2.set_ylim(0, 12)
    
    plt.title(f"Wellness Progress: {user}")
    ax1.legend(loc='upper left'); ax2.legend(loc='upper right')
    plt.xticks(rotation=45); plt.tight_layout()
    return fig, "✅ Data saved successfully!"