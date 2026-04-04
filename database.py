import sqlite3
import random

# ============================================================
# БАЗА ДАННЫХ
# ============================================================

def init_db():
    """Создаём все таблицы при первом запуске бота."""
    conn = sqlite3.connect("shop.db")
    cur  = conn.cursor()

    # Пользователи: хранит всех, кто писал боту
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            tg_id         INTEGER UNIQUE,
            name          TEXT,
            phone         TEXT,
            address       TEXT,
            language      TEXT DEFAULT 'ru',
            client_number INTEGER,
            registered    INTEGER DEFAULT 0
        )
    """)

    # Товары: каталог магазина
    cur.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            article      TEXT UNIQUE,
            name         TEXT,
            description  TEXT,
            price        INTEGER,
            photo_main   TEXT,
            photos_extra TEXT DEFAULT '[]',
            in_stock     INTEGER DEFAULT 1
        )
    """)

    # Корзина: выбранные товары до оформления заказа
    cur.execute("""
        CREATE TABLE IF NOT EXISTS cart (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id    INTEGER,
            product_id INTEGER
        )
    """)

    # Заказы: история всех оформленных заказов
    cur.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id        INTEGER,
            items          TEXT,
            total          INTEGER,
            status         TEXT DEFAULT 'pending',
            receipt_photo  TEXT,
            delivery_price INTEGER DEFAULT 0,
            delivery_days  INTEGER DEFAULT 0,
            created_at     TEXT
        )
    """)

    conn.commit()
    conn.close()


def get_user(tg_id: int):
    """Возвращает пользователя по Telegram ID или None."""
    conn = sqlite3.connect("shop.db")
    conn.row_factory = sqlite3.Row
    cur  = conn.cursor()
    cur.execute("SELECT * FROM users WHERE tg_id = ?", (tg_id,))
    user = cur.fetchone()
    conn.close()
    return user


def get_product(article: str):
    """Возвращает товар по артикулу или None."""
    conn    = sqlite3.connect("shop.db")
    conn.row_factory = sqlite3.Row
    cur     = conn.cursor()
    cur.execute("SELECT * FROM products WHERE article = ?", (article,))
    product = cur.fetchone()
    conn.close()
    return product


def get_cart_items(user_id: int):
    """Возвращает список товаров в корзине пользователя."""
    conn = sqlite3.connect("shop.db")
    conn.row_factory = sqlite3.Row
    cur  = conn.cursor()
    cur.execute("""
        SELECT c.id AS cart_id, p.*
        FROM   cart c
        JOIN   products p ON c.product_id = p.id
        WHERE  c.user_id = ?
    """, (user_id,))
    items = cur.fetchall()
    conn.close()
    return items


def generate_article() -> str:
    """Генерирует уникальный 4-значный артикул."""
    conn = sqlite3.connect("shop.db")
    cur  = conn.cursor()
    while True:
        article = str(random.randint(1000, 9999))
        cur.execute("SELECT id FROM products WHERE article = ?", (article,))
        if not cur.fetchone():
            conn.close()
            return article
