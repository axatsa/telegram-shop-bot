# ============================================================
# СОСТОЯНИЯ ПОЛЬЗОВАТЕЛЕЙ (вместо FSM)
# Храним в обычном словаре: {user_id: {"state": "...", "data": {}}}
# ============================================================

user_states: dict[int, dict] = {}

# Константы состояний — регистрация
S_LANG     = "S_LANG"
S_PHONE    = "S_PHONE"
S_NAME     = "S_NAME"
S_LOCATION = "S_LOCATION"
S_ADDRESS  = "S_ADDRESS"

# Магазин
S_ENTER_ID = "S_ENTER_ID"
S_RECEIPT  = "S_RECEIPT"

# Администратор
S_ADD_MAIN   = "S_ADD_MAIN"
S_ADD_EXTRA  = "S_ADD_EXTRA"
S_ADD_NAME   = "S_ADD_NAME"
S_ADD_DESC   = "S_ADD_DESC"
S_ADD_PRICE  = "S_ADD_PRICE"
S_EDIT_ART   = "S_EDIT_ART"
S_EDIT_FIELD = "S_EDIT_FIELD"
S_EDIT_VAL   = "S_EDIT_VAL"
S_ORDER_DEL  = "S_ORDER_DEL"
S_ORDER_CAN  = "S_ORDER_CAN"
S_BC_TEXT    = "S_BC_TEXT"
S_BC_PHOTO   = "S_BC_PHOTO"



def get_state(user_id: int) -> str | None:
    """Возвращает текущее состояние пользователя."""
    return user_states.get(user_id, {}).get("state")


def set_state(user_id: int, state: str):
    """Устанавливает состояние пользователя."""
    if user_id not in user_states:
        user_states[user_id] = {"state": None, "data": {}}
    user_states[user_id]["state"] = state


def clear_state(user_id: int):
    """Сбрасывает состояние и временные данные."""
    user_states[user_id] = {"state": None, "data": {}}


def set_data(user_id: int, key: str, value):
    """Сохраняет временные данные (например, фото при добавлении товара)."""
    if user_id not in user_states:
        user_states[user_id] = {"state": None, "data": {}}
    user_states[user_id]["data"][key] = value


def get_data(user_id: int) -> dict:
    """Возвращает все временные данные пользователя."""
    return user_states.get(user_id, {}).get("data", {})
