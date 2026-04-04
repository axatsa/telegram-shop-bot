import json
import sqlite3
from datetime import datetime
from telebot import types
from main import bot
from config import CARD_NUMBER, ADMIN_ID
from states import get_state, set_state, clear_state, S_ENTER_ID, S_RECEIPT
from database import get_product, get_cart_items, get_user
from keyboards import (kb_main_menu, kb_cancel, kb_product_inline, 
                       kb_cart_item_inline, kb_checkout_inline, kb_order_admin_inline)

# ============================================================
# ХЭНДЛЕРЫ — МАГАЗИН И КОРЗИНА
# ============================================================

@bot.message_handler(func=lambda m: m.text == "🛒 Сделать заказ")
def make_order(message: types.Message):
    """Просим ввести 4-значный артикул товара."""
    uid = message.from_user.id
    bot.send_message(uid, "🔍 Введите 4-значный ID товара:", reply_markup=kb_cancel())
    set_state(uid, S_ENTER_ID)


@bot.message_handler(func=lambda m: get_state(m.from_user.id) == S_ENTER_ID)
def search_product(message: types.Message):
    """Ищем товар по введённому артикулу."""
    uid = message.from_user.id

    if message.text == "❌ Отмена":
        clear_state(uid)
        bot.send_message(uid, "Главное меню:", reply_markup=kb_main_menu())
        return

    product = get_product(message.text.strip())

    if not product:
        bot.send_message(uid, "❌ Товар не найден. Попробуйте ещё раз:")
        return

    if not product["in_stock"]:
        bot.send_message(uid, "😔 Этот товар сейчас нет в наличии.")
        return

    caption = (
        f"📦 {product['name']}\n\n"
        f"📝 {product['description']}\n\n"
        f"💰 Цена: {product['price']:,} UZS\n"
        f"🏷 Артикул: {product['article']}"
    )

    extra_photos = json.loads(product["photos_extra"])

    if extra_photos:
        # Отправляем альбом фотографий
        media  = [types.InputMediaPhoto(product["photo_main"], caption=caption)]
        media += [types.InputMediaPhoto(ph) for ph in extra_photos[:3]]
        bot.send_media_group(uid, media)
        bot.send_message(uid, "Выберите действие:", reply_markup=kb_product_inline(product["article"]))
    else:
        bot.send_photo(
            uid,
            photo=product["photo_main"],
            caption=caption,
            reply_markup=kb_product_inline(product["article"])
        )

    clear_state(uid)


@bot.message_handler(func=lambda m: m.text == "🧺 Моя корзина")
def show_cart(message: types.Message):
    """Показываем содержимое корзины."""
    uid   = message.from_user.id
    items = get_cart_items(uid)

    if not items:
        bot.send_message(uid, "🧺 Ваша корзина пуста.", reply_markup=kb_main_menu())
        return

    total = sum(item["price"] for item in items)
    bot.send_message(uid, f"🧺 Ваша корзина ({len(items)} товаров):")

    for item in items:
        bot.send_message(
            uid,
            f"📦 {item['name']}\n🏷 {item['article']}  💰 {item['price']:,} UZS",
            reply_markup=kb_cart_item_inline(item["cart_id"], item["article"])
        )

    bot.send_message(uid, f"💰 Итого: {total:,} UZS", reply_markup=kb_checkout_inline())


@bot.message_handler(func=lambda m: m.text == "📦 Мои заказы")
def my_orders(message: types.Message):
    """История заказов пользователя."""
    uid  = message.from_user.id
    conn = sqlite3.connect("shop.db")
    conn.row_factory = sqlite3.Row
    cur  = conn.cursor()
    cur.execute("SELECT * FROM orders WHERE user_id=? ORDER BY id DESC LIMIT 10", (uid,))
    orders = cur.fetchall()
    conn.close()

    if not orders:
        bot.send_message(uid, "📦 У вас пока нет заказов.")
        return

    status_labels = {
        "pending":   "⏳ Ожидает",
        "confirmed": "✅ Подтверждён",
        "shipped":   "🚚 В пути",
        "cancelled": "❌ Отменён"
    }

    text = "📦 Ваши заказы:\n\n"
    for o in orders:
        label = status_labels.get(o["status"], o["status"])
        text += f"Заказ №{o['id']} — {label}\n💰 {o['total']:,} UZS | {o['created_at']}\n\n"

    bot.send_message(uid, text)


@bot.message_handler(func=lambda m: m.text == "👤 Мой профиль")
def my_profile(message: types.Message):
    uid  = message.from_user.id
    user = get_user(uid)
    if not user:
        bot.send_message(uid, "Профиль не найден. Введите /start")
        return
    bot.send_message(
        uid,
        f"👤 Ваш профиль\n\n"
        f"🏷 {user['name']}\n"
        f"📱 {user['phone']}\n"
        f"🏠 {user['address']}\n"
        f"🆔 Клиент №{user['client_number']}"
    )


# ============================================================
# CALLBACK-ХЭНДЛЕРЫ
# ============================================================

@bot.callback_query_handler(func=lambda c: c.data.startswith("add:"))
def add_to_cart(call: types.CallbackQuery):
    """Добавление товара в корзину."""
    article = call.data.split(":")[1]
    product = get_product(article)

    if not product:
        bot.answer_callback_query(call.id, "Товар не найден!", show_alert=True)
        return

    conn = sqlite3.connect("shop.db")
    cur  = conn.cursor()
    cur.execute("INSERT INTO cart (user_id, product_id) VALUES (?, ?)",
                (call.from_user.id, product["id"]))
    conn.commit()
    conn.close()

    bot.answer_callback_query(call.id, f"✅ [{article}] добавлен в корзину!", show_alert=True)


@bot.callback_query_handler(func=lambda c: c.data == "back")
def back_from_product(call: types.CallbackQuery):
    bot.send_message(call.from_user.id, "Введите ID товара или вернитесь в меню:", reply_markup=kb_main_menu())
    bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda c: c.data.startswith("del:"))
def remove_from_cart(call: types.CallbackQuery):
    """Удаление товара из корзины."""
    cart_id = int(call.data.split(":")[1])
    conn    = sqlite3.connect("shop.db")
    cur     = conn.cursor()
    cur.execute("DELETE FROM cart WHERE id = ?", (cart_id,))
    conn.commit()
    conn.close()

    bot.answer_callback_query(call.id, "❌ Товар удалён", show_alert=True)
    bot.delete_message(call.message.chat.id, call.message.message_id)


@bot.callback_query_handler(func=lambda c: c.data == "clear_cart")
def clear_cart_callback(call: types.CallbackQuery):
    """Очистка всей корзины."""
    conn = sqlite3.connect("shop.db")
    cur  = conn.cursor()
    cur.execute("DELETE FROM cart WHERE user_id = ?", (call.from_user.id,))
    conn.commit()
    conn.close()

    bot.answer_callback_query(call.id, "🗑 Корзина очищена", show_alert=True)
    bot.edit_message_text("🧺 Корзина очищена.", call.message.chat.id, call.message.message_id)


@bot.callback_query_handler(func=lambda c: c.data == "checkout")
def checkout(call: types.CallbackQuery):
    """Начало оформления заказа — показываем сумму и реквизиты."""
    uid   = call.from_user.id
    items = get_cart_items(uid)

    if not items:
        bot.answer_callback_query(call.id, "Корзина пуста!", show_alert=True)
        return

    total = sum(item["price"] for item in items)
    bot.send_message(
        uid,
        f"💳 Оформление заказа\n\n"
        f"💰 Сумма: {total:,} UZS\n\n"
        f"Переведите на карту:\n{CARD_NUMBER}\n\n"
        f"📸 После оплаты пришлите фото чека:",
        reply_markup=kb_cancel()
    )
    set_state(uid, S_RECEIPT)
    bot.answer_callback_query(call.id)


@bot.message_handler(func=lambda m: get_state(m.from_user.id) == S_RECEIPT and m.text == "❌ Отмена")
def cancel_checkout(message: types.Message):
    clear_state(message.from_user.id)
    bot.send_message(message.from_user.id, "Оформление отменено.", reply_markup=kb_main_menu())


@bot.message_handler(content_types=["photo"],
                     func=lambda m: get_state(m.from_user.id) == S_RECEIPT)
def receive_receipt(message: types.Message):
    """Получили фото чека — создаём заказ и уведомляем администратора."""
    uid   = message.from_user.id
    items = get_cart_items(uid)

    if not items:
        bot.send_message(uid, "Ошибка: корзина пуста.", reply_markup=kb_main_menu())
        clear_state(uid)
        return

    total         = sum(item["price"] for item in items)
    receipt_photo = message.photo[-1].file_id
    items_data    = [
        {"article": i["article"], "name": i["name"], "price": i["price"]}
        for i in items
    ]

    # Сохраняем заказ и очищаем корзину
    conn = sqlite3.connect("shop.db")
    cur  = conn.cursor()
    cur.execute("""
        INSERT INTO orders (user_id, items, total, receipt_photo, status, created_at)
        VALUES (?, ?, ?, ?, 'pending', ?)
    """, (uid, json.dumps(items_data, ensure_ascii=False), total,
          receipt_photo, datetime.now().strftime("%d.%m.%Y %H:%M")))
    order_id = cur.lastrowid
    cur.execute("DELETE FROM cart WHERE user_id=?", (uid,))
    conn.commit()
    conn.close()

    # Формируем сообщение для администратора
    user       = get_user(uid)
    items_text = "\n".join(f"• [{i['article']}] {i['name']} — {i['price']:,} UZS"
                           for i in items_data)

    admin_text = (
        f"🔔 Новый заказ №{order_id}\n\n"
        f"👤 Клиент №{user['client_number']}: {user['name']}\n"
        f"📱 {user['phone']}\n"
        f"🏠 {user['address']}\n\n"
        f"📦 Товары:\n{items_text}\n\n"
        f"💰 Сумма: {total:,} UZS"
    )

    bot.send_photo(
        ADMIN_ID,
        photo=receipt_photo,
        caption=admin_text,
        reply_markup=kb_order_admin_inline(order_id)
    )

    clear_state(uid)
    bot.send_message(
        uid,
        f"✅ Заказ №{order_id} принят!\nОжидайте подтверждения.",
        reply_markup=kb_main_menu()
    )
