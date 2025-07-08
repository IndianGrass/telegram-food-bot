import asyncio
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    ApplicationBuilder, CommandHandler,
    MessageHandler, ContextTypes, filters
)

# Вставь сюда свой токен от BotFather (для проверки)
TOKEN = "7864140185:AAHJAg-aEkxT0J4KSHeSJcleuGYDOZ7_1UY"

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

user_baskets = {}

def category_keyboard():
    keyboard = [[KeyboardButton(cat)] for cat in MENU.keys()]
    keyboard.append([KeyboardButton("🧺 Корзина"), KeyboardButton("🗑️ Очистить корзину")])
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def count_total(basket_items):
    kisses, hugs = 0, 0
    for item in basket_items:
        if "поцелуйчик" in item:
            kisses += int(item.split()[1])
        elif "обнимашк" in item:
            hugs += int(item.split()[1])
    return kisses, hugs

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Выбери категорию меню 👇", reply_markup=category_keyboard())

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

async def clear_basket(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_baskets[user_id] = []
    await update.message.reply_text("🗑️ Корзина очищена.")

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

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text

    print(f"Получено сообщение от {user_id}: {text}")  # Лог для проверки

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

# НЕ ЗАБУДЬ ПРО ОТСТУПЫ ↑↑↑


if __name__ == "__main__":
    try:
        loop = asyncio.get_event_loop()
        loop.create_task(main())
        loop.run_forever()
    except (KeyboardInterrupt, SystemExit):
        print("Бот остановлен вручную.")
