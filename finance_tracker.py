import sqlite3
from datetime import datetime
import os

def create_connection():
    conn = sqlite3.connect(os.path.join('instance', 'budget_tracker.db'))
    return conn

def create_tables():
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT UNIQUE,
                        password TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS transactions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER,
                        category TEXT,
                        amount REAL,
                        date TEXT,
                        type TEXT,
                        FOREIGN KEY(user_id) REFERENCES users(id))''')
    conn.commit()
    conn.close()

def register_user(username, password):
    conn = create_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, password))
        conn.commit()
    except sqlite3.IntegrityError:
        print("Username already exists.")
    conn.close()

def authenticate_user(username, password):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, password))
    user = cursor.fetchone()
    conn.close()
    return user

def add_transaction(user_id, category, amount, transaction_type):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO transactions (user_id, category, amount, date, type) VALUES (?, ?, ?, ?, ?)',
                   (user_id, category, amount, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), transaction_type))
    conn.commit()
    conn.close()

def generate_report(user_id, period='monthly'):
    conn = create_connection()
    cursor = conn.cursor()
    if period == 'monthly':
        query = '''SELECT SUM(amount) FROM transactions WHERE user_id = ? AND date >= ? AND date <= ?'''
        start_date = datetime.now().replace(day=1).strftime('%Y-%m-%d')
        end_date = datetime.now().strftime('%Y-%m-%d')
    elif period == 'yearly':
        query = '''SELECT SUM(amount) FROM transactions WHERE user_id = ? AND date >= ? AND date <= ?'''
        start_date = datetime.now().replace(month=1, day=1).strftime('%Y-%m-%d')
        end_date = datetime.now().strftime('%Y-%m-%d')
    cursor.execute(query, (user_id, start_date, end_date))
    total = cursor.fetchone()[0]
    conn.close()
    return total if total else 0
    