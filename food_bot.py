import asyncio
import os
import random
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    ApplicationBuilder, CommandHandler,
    MessageHandler, ContextTypes, filters
)

# Получаем токен из переменной окружения
TOKEN = os.getenv("BOT_TOKEN")

# Меню бота
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

# Хранилища данных пользователей
user_baskets = {}
user_history = {}
users = {}  # user_id -> {username, first_name}

# Клавиатура стартовая
def start_keyboard():
    return ReplyKeyboardMarkup(
        [[KeyboardButton("▶️ Старт")], [KeyboardButton("⛔ Стоп")]],
        resize_keyboard=True
    )

# Клавиатура с категориями меню
def category_keyboard():
    keyboard = [[KeyboardButton(cat)] for cat in MENU.keys()]
    keyboard.append([KeyboardButton("🧺 Корзина"), KeyboardButton("🗑️ Очистить корзину")])
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# Подсчёт итоговой стоимости
def count_total(basket_items):
    kisses, hugs = 0, 0
    for item in basket_items:
        try:
            if "поцелуйчик" in item:
                num = int(item.split()[-2])
                kisses += num
            elif "обнимашк" in item:
                num = int(item.split()[-2])
                hugs += num
        except (IndexError, ValueError):
            print(f"Не удалось распарсить: {item}")
    return kisses, hugs

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Нажми ▶️ Старт, чтобы выбрать еду, или ⛔ Стоп, чтобы выйти.",
        reply_markup=start_keyboard()
    )

# Отображение корзины
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

# Очистка корзины
async def clear_basket(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_baskets[user_id] = []
    await update.message.reply_text("🗑️ Корзина очищена.")

# Показ всех заказов
async def all_orders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not user_baskets:
        await update.message.reply_text("Пока никто ничего не заказал.")
        return

    text = "📋 Все заказы:\n"
    for user_id, basket in user_baskets.items():
        user_info = users.get(user_id)
        if user_info:
            name = user_info["username"] or user_info["first_name"] or f"ID {user_id}"
        else:
            name = f"ID {user_id}"

        kisses, hugs = count_total(basket)
        orders = "\n".join(f"   • {item}" for item in basket)
        summary = f"   💋 {kisses} поцелуйчиков, 🤗 {hugs} обнимашек"
        text += f"\n👤 {name}:\n{orders}\n{summary}\n"
    await update.message.reply_text(text)

# Показ личной истории заказов
async def show_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    history = user_history.get(user_id, [])
    if not history:
        await update.message.reply_text("📖 У вас пока нет истории заказов.")
    else:
        text = "📖 Ваша история заказов:\n" + "\n".join(f"• {item}" for item in history)
        await update.message.reply_text(text)

# Обработка сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username
    first_name = update.effective_user.first_name

    # Регистрируем пользователя
    if user_id not in users:
        users[user_id] = {"username": username, "first_name": first_name}

    text = update.message.text

    if text == "▶️ Старт":
        await update.message.reply_text("Выберите категорию меню 👇", reply_markup=category_keyboard())
        return

    elif text == "⛔ Стоп":
        await update.message.reply_text("До встречи! 🍽️", reply_markup=ReplyKeyboardMarkup([[]], resize_keyboard=True))
        return

    elif text == "🧺 Корзина":
        await basket(update, context)
        return

    elif text == "🗑️ Очистить корзину":
        await clear_basket(update, context)
        return

    elif text in MENU:
        dishes = MENU[text]
        keyboard = [[KeyboardButton(dish)] for dish in dishes]
        keyboard.append([KeyboardButton("⬅️ Назад")])
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(f"Выберите блюдо из категории {text}:", reply_markup=reply_markup)
        return

    elif text == "⬅️ Назад":
        await update.message.reply_text("Вернулись в главное меню 📅", reply_markup=category_keyboard())
        return

    else:
        for category, items in MENU.items():
            if text in items:
                price = items[text]
                user_baskets.setdefault(user_id, []).append(f"{text} — {price}")
                user_history.setdefault(user_id, []).append(f"{text} — {price}")
                await update.message.reply_text(f"✅ Добавлено в корзину: {text} ({price})")
                return
        await update.message.reply_text("❓ Не понял. Выбери из меню.")

# Главная точка запуска
async def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("basket", basket))
    app.add_handler(CommandHandler("clear", clear_basket))
    app.add_handler(CommandHandler("allorders", all_orders))
    app.add_handler(CommandHandler("history", show_history))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("🤖 Бот запущен...")

    await app.initialize()
    await app.start()
    await app.updater.start_polling()

if __name__ == "__main__":
    try:
        loop = asyncio.get_event_loop()
        loop.create_task(main())
        loop.run_forever()
    except (KeyboardInterrupt, SystemExit):
        print("Бот остановлен вручную.")
