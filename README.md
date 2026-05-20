# Telegram Shop Bot

A Telegram bot for an online shop — customers browse products by category, add items to cart, and place orders directly in Telegram.

## Features
- Product catalog organized by categories
- Shopping cart with quantity management
- Order placement and confirmation
- Admin order notifications
- SQLite database for products and orders

## Tech Stack
- Python 3.11+
- pyTelegramBotAPI (telebot)
- SQLite

## Setup
```bash
pip install -r requirements.txt
cp .env.example .env  # add BOT_TOKEN
python main.py
```