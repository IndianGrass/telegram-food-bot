import os
import logging
import aiohttp
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

logging.basicConfig(level=logging.INFO)

MENU = {
    "🍳 Завтрак": {
        "Яичница": "1 поцелуйчик",
        "Кофе": "1 обнимашка",
        "Омлет": "2 поцелуйчика",
        "Шоколадка": "3 обнимашки",
        "Печенье": "2 поцелуйчика",
        "Йогурт": "1 обнимашка",
        "Творог": "1 поцелуйчик",
        "Чай с мемами-котиками": "1 обнимашка"
    },
    "🥣 Обед": {
        "Борщ": "2 поцелуйчика",
        "Гороховый суп": "1 поцелуйчик",
        "Супец из Дыни": "3 обнимашки",
        "Рис": "2 поцелуйчика",
        "Овощи": "2 обнимашки",
        "Гречка": "2 обнимашки",
        "Спагетти": "3 поцелуйчика",
        "Жаренная картошечка": "3 поцелуйчика",
        "Рыбка": "3 обнимашки"
    },
    "🌙 Ужин": {
        "Рис": "2 поцелуйчика",
        "Овощи": "2 обнимашки",
        "Гречка": "2 обнимашки",
        "Спагетти": "3 поцелуйчика",
        "Жаренная картошечка": "3 поцелуйчика",
        "Рыбка": "3 обнимашки"
    },
    "🍕 Полезная еда": {
        "Пицца": "1 обнимашка и 3 поцелуя",
        "Чипсики": "3 поцелуя",
        "Пивасик": "1 поцелуй",
        "Вино": "10 поцелуев и 2 обнимашки",
        "Сходить в рестик": "50 поцелуйчиков"
    }
}

async def get_cat_meme_url(text: str) -> str:
    url = f"https://cataas.com/cat/says/{text}?json=true"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return "https://cataas.com" + data['url']
                else:
                    logging.error(f"HTTP error {resp.status} fetching meme")
                    return None
    except Exception as e:
        logging.error(f"Error fetching meme: {e}")
        return None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[KeyboardButton(cat)] for cat in MENU.keys()]
    keyboard.append([KeyboardButton("Стоп")])
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("Привет! Выбери категорию меню:", reply_markup=reply_markup)
    context.user_data.clear()

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_data = context.user_data

    if text == "Стоп":
        await update.message.reply_text("Бот остановлен. Чтобы начать заново, отправь /start.", reply_markup=ReplyKeyboardRemove())
        user_data.clear()
        return

    if "category" not in user_data:
        if text in MENU:
            user_data["category"] = text
            dishes = MENU[text]
            keyboard = [[KeyboardButton(dish)] for dish in dishes.keys()]
            keyboard.append([KeyboardButton("🔙 Назад")])
            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            await update.message.reply_text(f"Выбери блюдо из категории {text}:", reply_markup=reply_markup)
        else:
            await update.message.reply_text("Пожалуйста, выбери категорию из меню.")
        return

    if "category" in user_data:
        if text == "🔙 Назад":
            user_data.pop("category")
            await start(update, context)
            return

        category = user_data["category"]
        if text in MENU[category]:
            price = MENU[category][text]
            meme_url = await get_cat_meme_url(text)
            if meme_url:
                await update.message.reply_photo(meme_url, caption=f"✅ Добавлено в корзину: {text} — {price}")
            else:
                await update.message.reply_text(f"✅ Добавлено в корзину: {text} — {price}\n(мем не загрузился)")
        else:
            await update.message.reply_text("Пожалуйста, выбери блюдо из списка или нажми '🔙 Назад'.")

if __name__ == "__main__":
    import nest_asyncio
    import asyncio

    nest_asyncio.apply()

    TOKEN = os.getenv("BOT_TOKEN")
    if not TOKEN:
        raise RuntimeError("BOT_TOKEN не установлен в переменных окружения!")

    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Бот запущен...")
    asyncio.run(app.run_polling())
