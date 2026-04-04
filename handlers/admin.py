import json
import sqlite3
from telebot import types
from main import bot
from config import ADMIN_ID
from states import (get_state, set_state, get_data, set_data, clear_state,
                    S_ADD_MAIN, S_ADD_EXTRA, S_ADD_NAME, S_ADD_DESC, S_ADD_PRICE,
                    S_EDIT_ART, S_EDIT_FIELD, S_EDIT_VAL, S_ORDER_DEL, S_ORDER_CAN,
                    S_BC_TEXT, S_BC_PHOTO)
from database import get_product, generate_article
from keyboards import (kb_admin_menu, kb_cancel, kb_edit_fields_inline, 
                       kb_shipped_inline, kb_order_admin_inline)

# ============================================================
# ХЭНДЛЕРЫ — ПАНЕЛЬ АДМИНИСТРАТОРА
# ============================================================

# ---- Статистика ----

@bot.message_handler(func=lambda m: m.text == "📊 Статистика" and m.from_user.id == ADMIN_ID)
def admin_stats(message: types.Message):
    conn = sqlite3.connect("shop.db")
    cur  = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM users WHERE registered=1");         users_count = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM products WHERE in_stock=1");        prod_count  = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM orders");                           ord_count   = cur.fetchone()[0]
    cur.execute("SELECT SUM(total) FROM orders WHERE status='confirmed'"); revenue     = cur.fetchone()[0] or 0
    conn.close()

    bot.send_message(
        ADMIN_ID,
        f"📊 Статистика\n\n"
        f"👥 Клиентов: {users_count}\n"
        f"📦 Товаров в наличии: {prod_count}\n"
        f"🛒 Всего заказов: {ord_count}\n"
        f"💰 Выручка (подтверждённые): {revenue:,} UZS"
    )


# ---- Добавление товара (цепочка из 5 шагов) ----

@bot.message_handler(func=lambda m: m.text == "➕ Добавить товар" and m.from_user.id == ADMIN_ID)
def admin_add_start(message: types.Message):
    bot.send_message(ADMIN_ID, "📷 Отправьте главное фото товара:", reply_markup=kb_cancel())
    set_state(ADMIN_ID, S_ADD_MAIN)


@bot.message_handler(content_types=["photo"],
                     func=lambda m: m.from_user.id == ADMIN_ID and get_state(m.from_user.id) == S_ADD_MAIN)
def admin_got_main_photo(message: types.Message):
    set_data(ADMIN_ID, "photo_main",    message.photo[-1].file_id)
    set_data(ADMIN_ID, "photos_extra",  [])
    bot.send_message(ADMIN_ID, "📷 Отправьте доп. фото (до 3 шт). Когда закончите — напишите Готово:")
    set_state(ADMIN_ID, S_ADD_EXTRA)


@bot.message_handler(content_types=["photo", "text"],
                     func=lambda m: m.from_user.id == ADMIN_ID and get_state(m.from_user.id) == S_ADD_EXTRA)
def admin_got_extra_photos(message: types.Message):
    if message.text == "❌ Отмена":
        clear_state(ADMIN_ID)
        bot.send_message(ADMIN_ID, "Отменено.", reply_markup=kb_admin_menu())
        return

    if message.photo:
        extras = get_data(ADMIN_ID).get("photos_extra", [])
        if len(extras) < 3:
            extras.append(message.photo[-1].file_id)
            set_data(ADMIN_ID, "photos_extra", extras)
            bot.send_message(ADMIN_ID, f"✅ Фото {len(extras)}/3. Ещё или напишите Готово:")
        else:
            bot.send_message(ADMIN_ID, "Максимум 3 фото. Напишите Готово:")

    elif message.text == "Готово":
        bot.send_message(ADMIN_ID, "✏️ Введите название товара:")
        set_state(ADMIN_ID, S_ADD_NAME)


@bot.message_handler(func=lambda m: m.from_user.id == ADMIN_ID and get_state(m.from_user.id) == S_ADD_NAME)
def admin_got_name(message: types.Message):
    if message.text == "❌ Отмена":
        clear_state(ADMIN_ID)
        bot.send_message(ADMIN_ID, "Отменено.", reply_markup=kb_admin_menu())
        return
    set_data(ADMIN_ID, "name", message.text)
    bot.send_message(ADMIN_ID, "📝 Введите описание товара:")
    set_state(ADMIN_ID, S_ADD_DESC)


@bot.message_handler(func=lambda m: m.from_user.id == ADMIN_ID and get_state(m.from_user.id) == S_ADD_DESC)
def admin_got_desc(message: types.Message):
    if message.text == "❌ Отмена":
        clear_state(ADMIN_ID)
        bot.send_message(ADMIN_ID, "Отменено.", reply_markup=kb_admin_menu())
        return
    set_data(ADMIN_ID, "description", message.text)
    bot.send_message(ADMIN_ID, "💰 Введите цену в UZS (только цифры):")
    set_state(ADMIN_ID, S_ADD_PRICE)


@bot.message_handler(func=lambda m: m.from_user.id == ADMIN_ID and get_state(m.from_user.id) == S_ADD_PRICE)
def admin_got_price(message: types.Message):
    if message.text == "❌ Отмена":
        clear_state(ADMIN_ID)
        bot.send_message(ADMIN_ID, "Отменено.", reply_markup=kb_admin_menu())
        return

    if not message.text.isdigit():
        bot.send_message(ADMIN_ID, "❌ Введите только цифры!")
        return

    data    = get_data(ADMIN_ID)
    article = generate_article()

    conn = sqlite3.connect("shop.db")
    cur  = conn.cursor()
    cur.execute("""
        INSERT INTO products (article, name, description, price, photo_main, photos_extra)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (article, data["name"], data["description"], int(message.text),
          data["photo_main"], json.dumps(data.get("photos_extra", []))))
    conn.commit()
    conn.close()

    clear_state(ADMIN_ID)
    bot.send_message(
        ADMIN_ID,
        f"✅ Товар добавлен!\nАртикул: {article}\n📦 {data['name']}",
        reply_markup=kb_admin_menu()
    )


# ---- Редактирование товара ----

@bot.message_handler(func=lambda m: m.text == "✏️ Изменить товар" and m.from_user.id == ADMIN_ID)
def admin_edit_start(message: types.Message):
    bot.send_message(ADMIN_ID, "Введите артикул товара:", reply_markup=kb_cancel())
    set_state(ADMIN_ID, S_EDIT_ART)


@bot.message_handler(func=lambda m: m.from_user.id == ADMIN_ID and get_state(m.from_user.id) == S_EDIT_ART)
def admin_edit_find(message: types.Message):
    if message.text == "❌ Отмена":
        clear_state(ADMIN_ID)
        bot.send_message(ADMIN_ID, "Отменено.", reply_markup=kb_admin_menu())
        return

    product = get_product(message.text.strip())
    if not product:
        bot.send_message(ADMIN_ID, "❌ Товар не найден.")
        return

    set_data(ADMIN_ID, "edit_article", message.text.strip())
    bot.send_message(
        ADMIN_ID,
        f"Товар: {product['name']} [{product['article']}]\n"
        f"💰 {product['price']:,} UZS | {'✅ В наличии' if product['in_stock'] else '❌ Нет в наличии'}\n\n"
        f"Что изменить?",
        reply_markup=kb_edit_fields_inline()
    )
    set_state(ADMIN_ID, S_EDIT_FIELD)


@bot.callback_query_handler(func=lambda c: c.data.startswith("ef:") and c.from_user.id == ADMIN_ID)
def admin_edit_choose(call: types.CallbackQuery):
    field   = call.data.split(":")[1]
    article = get_data(ADMIN_ID).get("edit_article")

    if field in ("in", "out"):
        # Мгновенно меняем статус наличия
        value = 1 if field == "in" else 0
        conn  = sqlite3.connect("shop.db")
        cur   = conn.cursor()
        cur.execute("UPDATE products SET in_stock=? WHERE article=?", (value, article))
        conn.commit()
        conn.close()

        label = "в наличии ✅" if value else "снят с продажи 🔴"
        bot.send_message(ADMIN_ID, f"Товар помечен как {label}.", reply_markup=kb_admin_menu())
        clear_state(ADMIN_ID)
    else:
        set_data(ADMIN_ID, "edit_field", field)
        prompts = {
            "name":        "Введите новое название:",
            "description": "Введите новое описание:",
            "price":       "Введите новую цену (UZS):",
            "photo":       "Отправьте новое главное фото:"
        }
        bot.send_message(ADMIN_ID, prompts[field])
        set_state(ADMIN_ID, S_EDIT_VAL)

    bot.answer_callback_query(call.id)


@bot.message_handler(content_types=["photo", "text"],
                     func=lambda m: m.from_user.id == ADMIN_ID and get_state(m.from_user.id) == S_EDIT_VAL)
def admin_edit_save(message: types.Message):
    data    = get_data(ADMIN_ID)
    article = data.get("edit_article")
    field   = data.get("edit_field")

    conn = sqlite3.connect("shop.db")
    cur  = conn.cursor()

    if field == "photo":
        if not message.photo:
            bot.send_message(ADMIN_ID, "❌ Пришлите фото!")
            return
        cur.execute("UPDATE products SET photo_main=? WHERE article=?",
                    (message.photo[-1].file_id, article))

    elif field == "price":
        if not message.text.isdigit():
            bot.send_message(ADMIN_ID, "❌ Только цифры!")
            return
        cur.execute("UPDATE products SET price=? WHERE article=?", (int(message.text), article))

    elif field == "name":
        cur.execute("UPDATE products SET name=? WHERE article=?", (message.text, article))

    elif field == "description":
        cur.execute("UPDATE products SET description=? WHERE article=?", (message.text, article))

    conn.commit()
    conn.close()
    clear_state(ADMIN_ID)
    bot.send_message(ADMIN_ID, "✅ Товар обновлён!", reply_markup=kb_admin_menu())


# ---- Обработка заказов ----

@bot.callback_query_handler(func=lambda c: c.data.startswith("ok:") and c.from_user.id == ADMIN_ID)
def admin_confirm_order(call: types.CallbackQuery):
    """Администратор нажал «Подтвердить» — запрашиваем условия доставки."""
    order_id = int(call.data.split(":")[1])
    set_data(ADMIN_ID, "order_id", order_id)

    bot.send_message(
        ADMIN_ID,
        "✅ Введите стоимость доставки и срок через запятую:\n"
        "Пример: 15000, 3  (сумма UZS, дней)"
    )
    set_state(ADMIN_ID, S_ORDER_DEL)
    bot.answer_callback_query(call.id)


@bot.message_handler(func=lambda m: m.from_user.id == ADMIN_ID and get_state(m.from_user.id) == S_ORDER_DEL)
def admin_delivery_info(message: types.Message):
    """Сохраняем условия доставки и отправляем клиенту финальный чек."""
    try:
        parts          = message.text.replace(" ", "").split(",")
        delivery_price = int(parts[0])
        delivery_days  = int(parts[1])
    except Exception:
        bot.send_message(ADMIN_ID, "❌ Неверный формат. Пример: 15000, 3")
        return

    order_id = get_data(ADMIN_ID)["order_id"]
    conn     = sqlite3.connect("shop.db")
    conn.row_factory = sqlite3.Row
    cur      = conn.cursor()
    cur.execute("SELECT * FROM orders WHERE id=?", (order_id,))
    order    = cur.fetchone()
    cur.execute("""
        UPDATE orders SET status='confirmed', delivery_price=?, delivery_days=?
        WHERE id=?
    """, (delivery_price, delivery_days, order_id))
    conn.commit()
    conn.close()

    grand_total = order["total"] + delivery_price

    # Уведомляем клиента
    bot.send_message(
        order["user_id"],
        f"✅ Заказ №{order_id} подтверждён!\n\n"
        f"💰 Товары: {order['total']:,} UZS\n"
        f"🚚 Доставка: {delivery_price:,} UZS\n"
        f"💳 Итого: {grand_total:,} UZS\n\n"
        f"⏱ Срок доставки: {delivery_days} дней\n"
        f"📅 Дата заказа: {order['created_at']}"
    )

    clear_state(ADMIN_ID)
    bot.send_message(
        ADMIN_ID,
        f"✅ Заказ №{order_id} подтверждён. Клиент уведомлён.",
        reply_markup=kb_shipped_inline(order_id)
    )


@bot.callback_query_handler(func=lambda c: c.data.startswith("no:") and c.from_user.id == ADMIN_ID)
def admin_cancel_order(call: types.CallbackQuery):
    """Администратор нажал «Отмена» — запрашиваем причину."""
    order_id = int(call.data.split(":")[1])
    set_data(ADMIN_ID, "order_id", order_id)

    bot.send_message(ADMIN_ID, "❌ Введите причину отмены:")
    set_state(ADMIN_ID, S_ORDER_CAN)
    bot.answer_callback_query(call.id)


@bot.message_handler(func=lambda m: m.from_user.id == ADMIN_ID and get_state(m.from_user.id) == S_ORDER_CAN)
def admin_send_cancel_reason(message: types.Message):
    """Отправляем причину отмены клиенту."""
    order_id = get_data(ADMIN_ID)["order_id"]
    conn     = sqlite3.connect("shop.db")
    conn.row_factory = sqlite3.Row
    cur      = conn.cursor()
    cur.execute("SELECT * FROM orders WHERE id=?", (order_id,))
    order    = cur.fetchone()
    cur.execute("UPDATE orders SET status='cancelled' WHERE id=?", (order_id,))
    conn.commit()
    conn.close()

    bot.send_message(
        order["user_id"],
        f"❌ Заказ №{order_id} отменён.\n\nПричина: {message.text}"
    )
    clear_state(ADMIN_ID)
    bot.send_message(ADMIN_ID, f"Заказ №{order_id} отменён.", reply_markup=kb_admin_menu())


@bot.callback_query_handler(func=lambda c: c.data.startswith("ship:") and c.from_user.id == ADMIN_ID)
def mark_shipped(call: types.CallbackQuery):
    """Отмечаем заказ как отправленный и уведомляем клиента."""
    order_id = int(call.data.split(":")[1])
    conn     = sqlite3.connect("shop.db")
    conn.row_factory = sqlite3.Row
    cur      = conn.cursor()
    cur.execute("UPDATE orders SET status='shipped' WHERE id=?", (order_id,))
    cur.execute("SELECT user_id FROM orders WHERE id=?", (order_id,))
    order = cur.fetchone()
    conn.commit()
    conn.close()

    bot.send_message(order["user_id"], f"🚚 Ваш заказ №{order_id} отправлен! Ожидайте доставку.")
    bot.answer_callback_query(call.id, "🚚 Клиент уведомлён!", show_alert=True)


# ---- Рассылка ----

@bot.message_handler(func=lambda m: m.text == "📢 Рассылка" and m.from_user.id == ADMIN_ID)
def admin_broadcast_start(message: types.Message):
    bot.send_message(ADMIN_ID, "📢 Введите текст рассылки:", reply_markup=kb_cancel())
    set_state(ADMIN_ID, S_BC_TEXT)


@bot.message_handler(func=lambda m: m.from_user.id == ADMIN_ID and get_state(m.from_user.id) == S_BC_TEXT)
def admin_broadcast_text(message: types.Message):
    if message.text == "❌ Отмена":
        clear_state(ADMIN_ID)
        bot.send_message(ADMIN_ID, "Отменено.", reply_markup=kb_admin_menu())
        return
    set_data(ADMIN_ID, "broadcast_text", message.text)
    bot.send_message(ADMIN_ID, "📷 Отправьте фото или напишите Без фото:")
    set_state(ADMIN_ID, S_BC_PHOTO)


@bot.message_handler(content_types=["photo", "text"],
                     func=lambda m: m.from_user.id == ADMIN_ID and get_state(m.from_user.id) == S_BC_PHOTO)
def admin_broadcast_send(message: types.Message):
    text     = get_data(ADMIN_ID)["broadcast_text"]
    photo_id = message.photo[-1].file_id if message.photo else None

    # Берём всех зарегистрированных пользователей
    conn = sqlite3.connect("shop.db")
    cur  = conn.cursor()
    cur.execute("SELECT tg_id FROM users WHERE registered=1")
    users = cur.fetchall()
    conn.close()

    sent = 0
    for (tg_id,) in users:
        try:
            if photo_id:
                bot.send_photo(tg_id, photo=photo_id, caption=text)
            else:
                bot.send_message(tg_id, text)
            sent += 1
        except Exception:
            pass  # Пользователь заблокировал бота — пропускаем

    clear_state(ADMIN_ID)
    bot.send_message(
        ADMIN_ID,
        f"✅ Рассылка отправлена {sent} из {len(users)} пользователям.",
        reply_markup=kb_admin_menu()
    )
