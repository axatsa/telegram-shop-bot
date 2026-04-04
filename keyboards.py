from telebot import types

# ============================================================
# КЛАВИАТУРЫ
# ============================================================

def kb_language():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("🇷🇺 Русский", "🇺🇿 O'zbek")
    return kb


def kb_phone():
    kb  = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn = types.KeyboardButton("📱 Отправить номер", request_contact=True)
    kb.add(btn)
    return kb


def kb_location():
    kb  = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn = types.KeyboardButton("📍 Отправить геопозицию", request_location=True)
    kb.add(btn)
    kb.add("◀️ Назад")
    return kb


def kb_cancel():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("❌ Отмена")
    return kb


def kb_main_menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("🛒 Сделать заказ", "🧺 Моя корзина")
    kb.row("📦 Мои заказы",    "👤 Мой профиль")
    kb.add("❓ Помощь")
    return kb


def kb_admin_menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("➕ Добавить товар", "✏️ Изменить товар")
    kb.row("📢 Рассылка",       "📊 Статистика")
    kb.add("🏠 Главное меню")
    return kb


def kb_product_inline(article: str):
    """Inline-кнопки под карточкой товара."""
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("🛒 В корзину", callback_data=f"add:{article}"))
    kb.add(types.InlineKeyboardButton("◀️ Назад",    callback_data="back"))
    return kb


def kb_cart_item_inline(cart_id: int, article: str):
    """Кнопка удаления одного товара из корзины."""
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(f"❌ Удалить [{article}]", callback_data=f"del:{cart_id}"))
    return kb


def kb_checkout_inline():
    """Кнопки внизу корзины."""
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("💳 Оформить заказ",   callback_data="checkout"))
    kb.add(types.InlineKeyboardButton("🗑 Очистить корзину", callback_data="clear_cart"))
    return kb


def kb_order_admin_inline(order_id: int):
    """Кнопки для администратора под фото чека."""
    kb = types.InlineKeyboardMarkup()
    kb.row(
        types.InlineKeyboardButton("✅ Подтвердить", callback_data=f"ok:{order_id}"),
        types.InlineKeyboardButton("❌ Отмена",      callback_data=f"no:{order_id}")
    )
    return kb


def kb_shipped_inline(order_id: int):
    """Кнопка «Отправлено» после подтверждения заказа."""
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("🚚 Отметить как отправлено", callback_data=f"ship:{order_id}"))
    return kb


def kb_edit_fields_inline():
    """Кнопки выбора поля для редактирования товара."""
    kb = types.InlineKeyboardMarkup()
    kb.row(
        types.InlineKeyboardButton("📝 Название",    callback_data="ef:name"),
        types.InlineKeyboardButton("💬 Описание",    callback_data="ef:description")
    )
    kb.row(
        types.InlineKeyboardButton("💰 Цена",        callback_data="ef:price"),
        types.InlineKeyboardButton("📷 Фото",        callback_data="ef:photo")
    )
    kb.row(
        types.InlineKeyboardButton("🔴 Нет в наличии", callback_data="ef:out"),
        types.InlineKeyboardButton("🟢 В наличии",     callback_data="ef:in")
    )
    return kb
