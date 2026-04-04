from telebot import types
import sqlite3
from main import bot
from states import get_state, set_state, get_data, set_data, clear_state, S_LANG, S_PHONE, S_NAME, S_LOCATION, S_ADDRESS
from database import get_user
from keyboards import kb_language, kb_phone, kb_location, kb_cancel, kb_main_menu

# ============================================================
# ХЭНДЛЕРЫ — РЕГИСТРАЦИЯ
# ============================================================

# ---- Шаг 1: выбор языка ----

@bot.message_handler(func=lambda m: get_state(m.from_user.id) == S_LANG)
def reg_language(message: types.Message):
    uid = message.from_user.id

    if message.text == "🇷🇺 Русский":
        lang = "ru"
    elif message.text == "🇺🇿 O'zbek":
        lang = "uz"
    else:
        bot.send_message(uid, "Выберите язык из кнопок ниже.")
        return

    set_data(uid, "language", lang)
    text = "📱 Отправьте ваш номер телефона:" if lang == "ru" else "📱 Telefon raqamingizni yuboring:"
    bot.send_message(uid, text, reply_markup=kb_phone())
    set_state(uid, S_PHONE)


# ---- Шаг 2: номер телефона ----

@bot.message_handler(content_types=["contact"],
                     func=lambda m: get_state(m.from_user.id) == S_PHONE)
def reg_phone(message: types.Message):
    uid  = message.from_user.id
    lang = get_data(uid).get("language", "ru")

    set_data(uid, "phone", message.contact.phone_number)
    text = "✏️ Введите ваше Имя и Фамилию:" if lang == "ru" else "✏️ Ism va familiyangizni kiriting:"
    bot.send_message(uid, text, reply_markup=types.ReplyKeyboardRemove())
    set_state(uid, S_NAME)


# ---- Шаг 3: имя и фамилия ----

@bot.message_handler(func=lambda m: get_state(m.from_user.id) == S_NAME)
def reg_name(message: types.Message):
    uid  = message.from_user.id
    lang = get_data(uid).get("language", "ru")

    set_data(uid, "name", message.text)
    text = "📍 Отправьте вашу геопозицию:" if lang == "ru" else "📍 Joylashuvingizni yuboring:"
    bot.send_message(uid, text, reply_markup=kb_location())
    set_state(uid, S_LOCATION)


# ---- Шаг 4: геопозиция ----

@bot.message_handler(content_types=["location"],
                     func=lambda m: get_state(m.from_user.id) == S_LOCATION)
def reg_location(message: types.Message):
    uid  = message.from_user.id
    lang = get_data(uid).get("language", "ru")

    set_data(uid, "lat", message.location.latitude)
    set_data(uid, "lon", message.location.longitude)
    text = "🏠 Введите адрес (дом/подъезд/этаж):" if lang == "ru" else "🏠 Manzil kiriting (uy/podyezd/qavat):"
    bot.send_message(uid, text, reply_markup=kb_cancel())
    set_state(uid, S_ADDRESS)


@bot.message_handler(func=lambda m: get_state(m.from_user.id) == S_LOCATION and m.text == "◀️ Назад")
def reg_location_back(message: types.Message):
    """Кнопка 'Назад' на шаге геолокации."""
    uid  = message.from_user.id
    lang = get_data(uid).get("language", "ru")
    text = "✏️ Введите ваше Имя и Фамилию:" if lang == "ru" else "✏️ Ism va familiyangizni kiriting:"
    bot.send_message(uid, text, reply_markup=types.ReplyKeyboardRemove())
    set_state(uid, S_NAME)


# ---- Шаг 5: адрес (финальный шаг регистрации) ----

@bot.message_handler(func=lambda m: get_state(m.from_user.id) == S_ADDRESS)
def reg_address(message: types.Message):
    uid = message.from_user.id

    if message.text == "❌ Отмена":
        # Возвращаем на шаг геопозиции
        bot.send_message(uid, "📍 Отправьте геопозицию:", reply_markup=kb_location())
        set_state(uid, S_LOCATION)
        return

    data = get_data(uid)
    conn = sqlite3.connect("shop.db")
    cur  = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM users WHERE registered=1")
    client_number = cur.fetchone()[0] + 1

    cur.execute("""
        UPDATE users
        SET name=?, phone=?, address=?, language=?, client_number=?, registered=1
        WHERE tg_id=?
    """, (data["name"], data["phone"], message.text,
          data.get("language", "ru"), client_number, uid))
    conn.commit()
    conn.close()

    clear_state(uid)
    bot.send_message(
        uid,
        f"✅ Регистрация завершена!\nВы — Клиент №{client_number}\n\nДобро пожаловать в магазин! 🛍",
        reply_markup=kb_main_menu()
    )
