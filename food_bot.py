import os
import asyncio
import logging
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    ApplicationBuilder, CommandHandler,
    MessageHandler, ContextTypes, filters
)

# Логирование
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# 🔑 Токен из переменной окружения (или впиши вручную)
TOKEN = os.getenv("BOT_TOKEN")
# Временно можно вставить прямо сюда (если переменная не срабатывает)
# TOKEN = "вставь_сюда_токен_от_BotFather"

# Меню
MENU = {
    "🥣 Первое": {
        "Гороховый суп": "1 поцелуйчик",
        "Борщ": "2 поцелуйчика",
        "Супец из Дыни": "3 обнимашки"
    },
    "🍗 Второе": {
        "Жаренная картошечка": "3 поцелуйчика",
        "Гречка": "2 обнимашки",
        "Рис": "2 поцелуйчика",
        "Плов": "3 обнимашки",
        "Макарошки": "1 поцелуйчик",
        "Омлет": "2 поцелуйчика"
    },
    "🥤 Напитки": {
        "Кофе": "1 обнимашка",
        "Чай-чай-выручай": "1 поцелуйчик",
        "Водаааа": "бесплатно 💧"
    }
}

# Корзины пользователей
user_baskets = {}

# Клавиатура категорий
def category_keyboard():
    keyboard = [[KeyboardButton(cat)] for cat in MENU.keys()]
    keyboard.append([KeyboardButton("🧺 Корзина"), KeyboardButton("🗑️ Очистить корзину")])
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# Подсчёт итогов
def count_total(basket_items):
    kisses, hugs = 0, 0
    for item in basket_items:
        if "поцелуйчик" in item:
            kisses += int(item.split()[1])
        elif "обнимашк" in item:
            hugs += int(item.split()[1])
    return kisses, hugs

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Выбери категорию меню 👇", reply_markup=category_keyboard())

# Показать корзину
async def basket(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    items = user_baskets.get(user_id, [])
    if not items:
        await update.message.reply_text("🧺 Ваша корзина пуста.")
    else:
        kisses, hugs = count_total(items)
        text = "🧺 Ваш заказ:\n" + "\n".join(f"• {item}" for item in items)
        text += f"\n\n💋 Поцелуйчиков: {kisses}\n🤗 Обнимашек: {hugs}"
        await update.message.reply_text(text)

# Очистить корзину
async def clear_basket(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_baskets[user_id] = []
    await update.message.reply_text("🗑️ Корзина очищена.")

# Все заказы
async def all_orders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not user_baskets:
        await update.message.reply_text("Пока никто ничего не заказал.")
        return
    text = "📋 Все заказы:\n"
    for user_id, basket in user_baskets.items():
        name = f"👤 Пользователь {user_id}"
        kisses, hugs = count_total(basket)
        orders = "\n".join(f"   • {item}" for item in basket)
        summary = f"   💋 {kisses} поцелуйчиков, 🤗 {hugs} обнимашек"
        text += f"\n{name}:\n{orders}\n{summary}\n"
    await update.message.reply_text(text)

# Обработка всех сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text

    print(f"Получено сообщение от {user_id}: {text}")  # Для логов

    if text == "🔙 Назад":
        await start(update, context)
    elif text == "🧺 Корзина":
        await basket(update, context)
    elif text == "🗑️ Очистить корзину":
        await clear_basket(update, context)
    elif text in MENU:
        dishes = MENU[text]
        keyboard = [[KeyboardButton(dish)] for dish in dishes]
        keyboard.append([KeyboardButton("🔙 Назад")])
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(f"Выберите блюдо из категории {text}:", reply_markup=reply_markup)
    else:
        for category, items in MENU.items():
            if text in items:
                price = items[text]
                user_baskets.setdefault(user_id, []).append(f"{text} — {price}")
                await update.message.reply_text(f"✅ Добавлено в корзину: {text} ({price})")
                return
        await update.message.reply_text("❓ Не понял. Выбери из меню.")

# Основной запуск
async def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("basket", basket))
    app.add_handler(CommandHandler("clear", clear_basket))
    app.add_handler(CommandHandler("allorders", all_orders))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("🤖 Бот запущен...")

    await app.initialize()
    await app.start()
    await app.updater.start_polling()

    # ✨ Важно: не даём Railway завершить контейнер
    loop = asyncio.get_event_loop()
    loop.run_forever()

# Запуск
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except RuntimeError as e:
        if "already running" in str(e):
            loop = asyncio.get_event_loop()
            loop.create_task(main())
            loop.run_forever()
        else:
            raise
