import telebot
from config import BOT_TOKEN
from database import init_db

# ============================================================
# TELEGRAM BOT — ИНТЕРНЕТ-МАГАЗИН
# ============================================================

# Инициализация бота
bot = telebot.TeleBot(BOT_TOKEN)

# Импортируем хэндлеры ПОСЛЕ создания бота
import handlers

if __name__ == "__main__":
    init_db()
    print("🤖 Бот запущен. Нажмите Ctrl+C для остановки.")
    try:
        bot.infinity_polling()
    except Exception as e:
        print(f"❌ Ошибка: {e}")