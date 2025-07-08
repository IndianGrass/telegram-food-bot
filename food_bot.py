import os
import random
import nest_asyncio
nest_asyncio.apply()

import asyncio
from telegram import (
    Update, ReplyKeyboardMarkup, KeyboardButton
)
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ContextTypes, filters
)

TOKEN = os.getenv("BOT_TOKEN")  # Токен из переменной окружения

MENU = {
    "🍳 Завтрак": {
        "Яичница": ("1 поцелуйчик", ),
        "Кофе": ("1 обнимашка", ),
        "Омлет": ("2 поцелуйчика", ),
        "Шоколадка": ("3 обнимашки", ),
        "Печенье": ("2 поцелуйчика", ),
        "Йогурт": ("1 обнимашка", ),
        "Творог": ("1 поцелуйчик", ),
        "Чай с мемами-котиками": ("1 обнимашка", )
    },
    "🥣 Обед": {
        "Первое": {
            "Борщ": ("2 поцелуйчика", ),
            "Гороховый суп": ("1 поцелуйчик", ),
            "Супец из Дыни": ("3 обнимашки", )
        },
        "Второе": {
            "Рис": ("2 поцелуйчика", ),
            "Овощи": ("2 обнимашки", ),
            "Гречка": ("2 обнимашки", ),
            "Спагетти": ("3 поцелуйчика", ),
            "Жаренная картошечка": ("3 поцелуйчика", ),
            "Рыбка": ("3 обнимашки", )
        }
    },
    "🌙 Ужин": {
        "Рис": ("2 поцелуйчика", ),
        "Овощи": ("2 обнимашки", ),
        "Гречка": ("2 обнимашки", ),
        "Спагетти": ("3 поцелуйчика", ),
        "Жаренная картошечка": ("3 поцелуйчика", ),
        "Рыбка": ("3 обнимашки", )
    },
    "🍕 \"Полезная еда\"": {
        "Пицца": ("1 обнимашка и 3 поцелуя", ),
        "Чипсики": ("3 поцелуя", ),
        "Пивасик": ("1 поцелуй", ),
        "Вино": ("10 поцелуев и 2 обнимашки", ),
        "Сходить в рестик": ("50 поцелуйчиков", )
    }
}

user_baskets = {}
order_history = {}

def get_main_keyboard():
    return ReplyKeyboardMarkup(
        [
            [KeyboardButton("Старт"), KeyboardButton("Стоп")],
            [KeyboardButton("🧺 Корзина"), KeyboardButton("🗑️ Очистить корзину")],
            [KeyboardButton("📜 История заказов")],
            [KeyboardButton("🔥 ТОП заказчиков")]
        ],
        resize_keyboard=True
    )

def category_keyboard():
    return ReplyKeyboardMarkup(
        [[KeyboardButton(cat)] for cat in MENU.keys()] + [[KeyboardButton("🔙 Назад")]],
        resize_keyboard=True
    )

def submenu_keyboard(submenu):
    return ReplyKeyboardMarkup(
        [[KeyboardButton(dish)] for dish in submenu.keys()] + [[KeyboardButton("🔙 Назад")]],
        resize_keyboard=True
    )

def count_total(items):
    kisses = 0
    hugs = 0
    for item in items:
        parts = item.split("—")
        if len(parts) < 2:
            continue
        price_text = parts[1].strip()
        if "обнимашка" in price_text:
            try:
                hugs += int(''.join(filter(str.isdigit, price_text)))
            except:
                pass
        if "поцелуй" in price_text:
            try:
                kisses += int(''.join(filter(str.isdigit, price_text)))
            except:
                pass
    return kisses, hugs

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Нажми 'Старт' чтобы открыть меню, или 'Стоп' чтобы остановить бота.",
        reply_markup=get_main_keyboard()
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username or update.effective_user.first_name or str(user_id)
    text = update.message.text

    def send_random_meme(item_str):
        meme_files = [f for f in os.listdir("memes") if f.lower().endswith((".jpg", ".jpeg", ".png"))]
        if meme_files:
            meme_path = os.path.join("memes", random.choice(meme_files))
            with open(meme_path, "rb") as photo:
                return update.message.reply_photo(photo, caption=f"✅ Добавлено в корзину: {item_str}")
        else:
            return update.message.reply_text(f"✅ Добавлено в корзину: {item_str}")

    if text == "Старт":
        await update.message.reply_text("Выбери категорию меню:", reply_markup=category_keyboard())

    elif text == "Стоп":
        await update.message.reply_text("Бот остановлен. Для старта нажми 'Старт'.", reply_markup=None)

    elif text == "🔙 Назад":
        await update.message.reply_text("Вернулись в главное меню.", reply_markup=get_main_keyboard())

    elif text == "🧺 Корзина":
        items = user_baskets.get(user_id, [])
        if not items:
            await update.message.reply_text("🧺 Ваша корзина пуста.")
        else:
            kisses, hugs = count_total(items)
            text_resp = "🧺 Ваш заказ:\n" + "\n".join(f"• {item}" for item in items)
            text_resp += f"\n\n💋 Поцелуйчиков: {kisses}\n🤗 Обнимашек: {hugs}"
            await update.message.reply_text(text_resp)

    elif text == "🗑️ Очистить корзину":
        user_baskets[user_id] = []
        await update.message.reply_text("🗑️ Корзина очищена.")

    elif text == "📜 История заказов":
        hist = order_history.get(user_id, [])
        if not hist:
            await update.message.reply_text("У вас ещё нет истории заказов.")
        else:
            text_resp = "📜 Ваша история заказов:\n" + "\n".join(hist)
            await update.message.reply_text(text_resp)

    elif text == "🔥 ТОП заказчиков":
        top_users = []
        for uid, basket in order_history.items():
            kisses_total, hugs_total = count_total(basket)
            top_users.append((uid, kisses_total, hugs_total))
        top_users.sort(key=lambda x: (x[1] + x[2]), reverse=True)
        text_resp = "🔥 ТОП заказчиков:\n"
        for i, (uid, kisses_t, hugs_t) in enumerate(top_users[:10], 1):
            text_resp += f"{i}. Пользователь {uid}: 💋 {kisses_t}, 🤗 {hugs_t}\n"
        if not top_users:
            text_resp = "Пока никто не сделал заказов."
        await update.message.reply_text(text_resp)

    elif text in MENU.keys():
        if text == "🥣 Обед":
            keyboard = ReplyKeyboardMarkup(
                [[KeyboardButton("Первое")], [KeyboardButton("Второе")], [KeyboardButton("🔙 Назад")]],
                resize_keyboard=True
            )
            await update.message.reply_text("Выберите подкатегорию Обеда:", reply_markup=keyboard)
        else:
            dishes = MENU[text]
            if isinstance(dishes, dict):
                keyboard = submenu_keyboard(dishes)
                await update.message.reply_text(f"Выберите блюдо из {text}:", reply_markup=keyboard)
            else:
                await update.message.reply_text("Ошибка структуры меню.")

    elif text in MENU.get("🥣 Обед", {}).get("Первое", {}):
        dish = text
        price = MENU["🥣 Обед"]["Первое"][dish][0]
        item_str = f"{dish} — {price}"
        user_baskets.setdefault(user_id, []).append(item_str)
        order_history.setdefault(user_id, []).append(item_str)
        await send_random_meme(item_str)

    elif text in MENU.get("🥣 Обед", {}).get("Второе", {}):
        dish = text
        price = MENU["🥣 Обед"]["Второе"][dish][0]
        item_str = f"{dish} — {price}"
        user_baskets.setdefault(user_id, []).append(item_str)
        order_history.setdefault(user_id, []).append(item_str)
        await send_random_meme(item_str)

    else:
        found = False
        for cat, dishes in MENU.items():
            if isinstance(dishes, dict):
                for dish, data in dishes.items():
                    if isinstance(data, tuple) and dish == text:
                        price = data[0]
                        item_str = f"{dish} — {price}"
                        user_baskets.setdefault(user_id, []).append(item_str)
                        order_history.setdefault(user_id, []).append(item_str)
                        await send_random_meme(item_str)
                        found = True
                        break
            if found:
                break
        if not found:
            await update.message.reply_text("❓ Не понял, выберите из меню.")

async def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("🤖 Бот запущен...")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
