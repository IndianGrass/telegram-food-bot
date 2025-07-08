import os
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ContextTypes, filters
)

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
    keyboard.append([
        KeyboardButton("🧺 Корзина"),
        KeyboardButton("🗑️ Очистить корзину"),
        KeyboardButton("📋 Все заказы")
    ])
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Я — бот-меню. Выбери категорию блюда 👇",
        reply_markup=category_keyboard()
    )

def count_total(basket_items):
    kisses = 0
    hugs = 0
    for item in basket_items:
        if "поцелуйчик" in item:
            num = int(item.split()[1])
            kisses += num
        elif "обнимашк" in item:
            num = int(item.split()[1])
            hugs += num
    return kisses, hugs

async def basket(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    basket_items = user_baskets.get(user_id, [])
    if not basket_items:
        await update.message.reply_text("🧺 Ваша корзина пуста.")
    else:
        kisses, hugs = count_total(basket_items)
        text = "🧺 Ваш заказ:\n" + "\n".join(f"• {item}" for item in basket_items)
        text += f"\n\n💋 Поцелуйчиков: {kisses}\n🤗 Обнимашек: {hugs}"
        await update.message.reply_text(text)

async def clear_basket(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_baskets[user_id] = []
    await update.message.reply_text("🗑️ Ваша корзина очищена.")

async def all_orders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not user_baskets:
        await update.message.reply_text("Пока никто ничего не заказал.")
        return

    text = "📋 Все заказы:\n"
    for user_id, basket in user_baskets.items():
        kisses, hugs = count_total(basket)
        orders = "\n".join(f"   • {item}" for item in basket)
        summary = f"   💋 {kisses} поцелуйчиков, 🤗 {hugs} обнимашек"
        text += f"\n👤 Пользователь {user_id}:\n{orders}\n{summary}\n"
    await update.message.reply_text(text)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text

    if text == "🔙 Назад":
        await start(update, context)
        return

    if text == "🧺 Корзина":
        await basket(update, context)
        return

    if text == "🗑️ Очистить корзину":
        await clear_basket(update, context)
        return

    if text == "📋 Все заказы":
        await all_orders(update, context)
        return

    if text in MENU:
        dishes = MENU[text]
        keyboard = [[KeyboardButton(dish)] for dish in dishes.keys()]
        keyboard.append([KeyboardButton("🔙 Назад")])
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(f"Выберите блюдо из категории {text}:", reply_markup=reply_markup)
        return

    for category in MENU:
        if text in MENU[category]:
            price = MENU[category][text]
            user_baskets.setdefault(user_id, []).append(f"{text} — {price}")
            await update.message.reply_text(f"✅ Добавлено в корзину: {text} ({price})")
            return

    await update.message.reply_text("❓ Не понял. Выбери из меню.")

if __name__ == "__main__":
    import asyncio

    async def main():
        token = os.getenv("BOT_TOKEN")
        if not token:
            print("❌ Ошибка: переменная окружения BOT_TOKEN не найдена")
            return

        app = ApplicationBuilder().token(token).build()

        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("basket", basket))
        app.add_handler(CommandHandler("clear", clear_basket))
        app.add_handler(CommandHandler("allorders", all_orders))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

        print("🤖 Бот запущен...")
        await app.run_polling()

    asyncio.run(main())
