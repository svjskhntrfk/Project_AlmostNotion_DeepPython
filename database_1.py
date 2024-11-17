import sqlite3
from datetime import datetime

def connect_db():
    conn = sqlite3.connect('users.db')
    return conn

def create_table():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    conn.commit()
    conn.close()
    print("База данных и таблица успешно созданы.")


def is_email_registered(email):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM users WHERE email = ?', (email,))
    count = cursor.fetchone()[0]
    conn.close()
    return count > 0


def add_user(email, password):
    if is_email_registered(email):
        print("Ошибка: Пользователь с такой почтой уже зарегистрирован.")
        return

    conn = connect_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
        INSERT INTO users (email, password, created_at)
        VALUES (?, ?, ?)
        ''', (email, password, datetime.now()))
        conn.commit()
        print("Пользователь успешно добавлен!")
    except:
        Exception
    finally:
        conn.close()

def get_all_users():
    conn = connect_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM users')
    users = cursor.fetchall()
    
    conn.close()
    return users


