from telebot import types
import sqlite3
from main import bot
from config import ADMIN_ID
from states import clear_state, set_state, S_LANG
from database import get_user
from keyboards import kb_main_menu, kb_language, kb_admin_menu

# ============================================================
# ХЭНДЛЕРЫ — СТАРТ И ОБЩИЕ
# ============================================================

@bot.message_handler(commands=["start"])
def cmd_start(message: types.Message):
    """Точка входа. Проверяем, зарегистрирован ли пользователь."""
    uid  = message.from_user.id
    user = get_user(uid)
    clear_state(uid)

    if user and user["registered"]:
        # Уже зарегистрирован — показываем главное меню
        bot.send_message(
            uid,
            f"👋 С возвращением, {user['name']}!\nВы — Клиент №{user['client_number']}",
            reply_markup=kb_main_menu()
        )
    else:
        # Новый пользователь — создаём запись и начинаем регистрацию
        conn = sqlite3.connect("shop.db")
        cur  = conn.cursor()
        cur.execute("INSERT OR IGNORE INTO users (tg_id) VALUES (?)", (uid,))
        conn.commit()
        conn.close()

        bot.send_message(
            uid,
            "🌟 Добро пожаловать!\nWelcome!\n\nВыберите язык / Tilni tanlang:",
            reply_markup=kb_language()
        )
        set_state(uid, S_LANG)


@bot.message_handler(func=lambda m: m.text == "АДМИН")
def admin_secret(message: types.Message):
    """Если ID совпадает — открываем панель администратора."""
    if message.from_user.id == ADMIN_ID:
        bot.send_message(ADMIN_ID, "👑 Панель администратора:", reply_markup=kb_admin_menu())


@bot.message_handler(func=lambda m: m.text == "🏠 Главное меню")
def go_main_menu(message: types.Message):
    clear_state(message.from_user.id)
    bot.send_message(message.from_user.id, "Главное меню:", reply_markup=kb_main_menu())


@bot.message_handler(func=lambda m: m.text == "❓ Помощь")
def help_cmd(message: types.Message):
    bot.send_message(
        message.from_user.id,
        "❓ Помощь\n\n"
        "1️⃣ Нажмите «Сделать заказ» и введите 4-значный ID товара.\n"
        "2️⃣ Добавьте товары в корзину.\n"
        "3️⃣ Оформите заказ и оплатите по карте.\n"
        "4️⃣ Пришлите фото чека.\n"
        "5️⃣ Ожидайте подтверждения.\n\n"
        "По вопросам: @admin_username"
    )
