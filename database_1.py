import aiosqlite
from datetime import datetime
import asyncio


async def connect_db():
    print("Подключение к базе данных...")
    return await aiosqlite.connect('users.db')


async def create_table():
    print("Создание таблицы...")
    async with await connect_db() as conn:
        await conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        await conn.commit()
        print("База данных и таблица успешно созданы.")


async def is_email_registered(email):
    print(f"Проверка, зарегистрирован ли email: {email}")
    async with await connect_db() as conn:
        cursor = await conn.execute('SELECT email, password, created_at FROM users WHERE email = ?', (email,))
        user = await cursor.fetchone()
        print(f"Результат проверки: {user}")
        return user  # Возвращает None, если пользователь не найден


async def add_user(email, password):
    print(f"Добавление пользователя: {email}")
    user = await is_email_registered(email)
    if user:
        print(f"Ошибка: Пользователь с такой почтой уже зарегистрирован. Данные: {user}")
        return

    async with await connect_db() as conn:
        try:
            await conn.execute('''
            INSERT INTO users (email, password, created_at)
            VALUES (?, ?, ?)
            ''', (email, password, datetime.now()))
            await conn.commit()
            print(f"Пользователь {email} успешно добавлен!")
        except aiosqlite.IntegrityError as e:
            print(f"Ошибка: Не удалось добавить пользователя. Причина: {e}")


=


