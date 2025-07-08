import os
import asyncio
from telegram import (
    Update, ReplyKeyboardMarkup, KeyboardButton, InputMediaPhoto
)
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ContextTypes, filters, CallbackQueryHandler
)
from telegram.constants import ParseMode

TOKEN = os.getenv("BOT_TOKEN")  # Токен из переменной окружения

# Меню с категориями и блюдами с ценами и мемами (URL котиков)
MENU = {
    "🍳 Завтрак": {
        "Яичница": ("1 поцелуйчик", "https://i.imgur.com/0f7QyKx.jpg"),
        "Кофе": ("1 обнимашка", "https://i.imgur.com/LzAxGhr.jpg"),
        "Омлет": ("2 поцелуйчика", "https://i.imgur.com/H07v27c.jpg"),
        "Шоколадка": ("3 обнимашки", "https://i.imgur.com/DqkshM6.jpg"),
        "Печенье": ("2 поцелуйчика", "https://i.imgur.com/mj0xFvl.jpg"),
        "Йогурт": ("1 обнимашка", "https://i.imgur.com/pm7ZwwF.jpg"),
        "Творог": ("1 поцелуйчик", "https://i.imgur.com/tYl6vhR.jpg"),
        "Чай с мемами-котиками": ("1 обнимашка", "https://i.imgur.com/svQno44.jpg")
    },
    "🥣 Обед": {
        "Первое": {
            "Борщ": ("2 поцелуйчика", "https://i.imgur.com/kEYs60V.jpg"),
            "Гороховый суп": ("1 поцелуйчик", "https://i.imgur.com/NmEjZqA.jpg"),
            "Супец из Дыни": ("3 обнимашки", "https://i.imgur.com/gSLT2Kp.jpg")
        },
        "Второе": {
            "Рис": ("2 поцелуйчика", "https://i.imgur.com/YzmXS2p.jpg"),
            "Овощи": ("2 обнимашки", "https://i.imgur.com/VoLU50a.jpg"),
            "Гречка": ("2 обнимашки", "https://i.imgur.com/VoLU50a.jpg"),
            "Спагетти": ("3 поцелуйчика", "https://i.imgur.com/r4lYb8R.jpg"),
            "Жаренная картошечка": ("3 поцелуйчика", "https://i.imgur.com/Bsp37fz.jpg"),
            "Рыбка": ("3 обнимашки", "https://i.imgur.com/IfUpnWn.jpg")
        }
    },
    "🌙 Ужин": {
        "Рис": ("2 поцелуйчика", "https://i.imgur.com/YzmXS2p.jpg"),
        "Овощи": ("2 обнимашки", "https://i.imgur.com/VoLU50a.jpg"),
        "Гречка": ("2 обнимашки", "https://i.imgur.com/VoLU50a.jpg"),
        "Спагетти": ("3 поцелуйчика", "https://i.imgur.com/r4lYb8R.jpg"),
        "Жаренная картошечка": ("3 поцелуйчика", "https://i.imgur.com/Bsp37fz.jpg"),
        "Рыбка": ("3 обнимашки", "https://i.imgur.com/IfUpnWn.jpg")
    },
    "🍕 \"Полезная еда\"": {
        "Пицца": ("1 обнимашка и 3 поцелуя", "https://i.imgur.com/w9L62vK.jpg"),
        "Чипсики": ("3 поцелуя", "https://i.imgur.com/gd3HbXr.jpg"),
        "Пивасик": ("1 поцелуй", "https://i.imgur.com/j6Z9vR2.jpg"),
        "Вино": ("10 поцелуев и 2 обнимашки", "https://i.imgur.com/kG7UMbH.jpg"),
        "Сходить в рестик": ("50 поцелуйчиков", "https://i.imgur.com/6DLbdx8.jpg")
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
    # Категории меню (завтрак, обед, ужин, полезная еда)
    return ReplyKeyboardMarkup(
        [[KeyboardButton(cat)] for cat in MENU.keys()] + [[KeyboardButton("🔙 Назад")]],
        resize_keyboard=True
    )

def submenu_keyboard(submenu):
    # Создаёт клавиатуру из словаря блюд
    return ReplyKeyboardMarkup(
        [[KeyboardButton(dish)] for dish in submenu.keys()] + [[KeyboardButton("🔙 Назад")]],
        resize_keyboard=True
    )

def count_total(items):
    kisses = 0
    hugs = 0
    for item in items:
        # item как "Яичница — 1 поцелуйчик"
        parts = item.split("—")
        if len(parts) < 2:
            continue
        price_text = parts[1].strip()
        # Парсим числа из цены
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
        # Подсчёт поцелуев и обнимашек по всем юзерам
        top_users = []
        for uid, basket in order_history.items():
            kisses_total, hugs_total = count_total(basket)
            top_users.append((uid, kisses_total, hugs_total))
        top_users.sort(key=lambda x: (x[1]+x[2]), reverse=True)
        text_resp = "🔥 ТОП заказчиков:\n"
        for i, (uid, kisses_t, hugs_t) in enumerate(top_users[:10], 1):
            text_resp += f"{i}. Пользователь {uid}: 💋 {kisses_t}, 🤗 {hugs_t}\n"
        if not top_users:
            text_resp = "Пока никто не сделал заказов."
        await update.message.reply_text(text_resp)
    elif text in MENU.keys():
        # Категория из основного меню
        # Если категория Обед — два подкатегории (первое, второе)
        if text == "🥣 Обед":
            keyboard = ReplyKeyboardMarkup(
                [[KeyboardButton("Первое")], [KeyboardButton("Второе")], [KeyboardButton("🔙 Назад")]],
                resize_keyboard=True
            )
            await update.message.reply_text("Выберите подкатегорию Обеда:", reply_markup=keyboard)
        else:
            # Простой список блюд в категории
            dishes = MENU[text]
            if isinstance(dishes, dict):
                keyboard = submenu_keyboard(dishes)
                await update.message.reply_text(f"Выберите блюдо из {text}:", reply_markup=keyboard)
            else:
                # на всякий случай
                await update.message.reply_text("Ошибка структуры меню.")
    elif text in MENU.get("🥣 Обед", {}).get("Первое", {}):
        dish = text
        price, meme_url = MENU["🥣 Обед"]["Первое"][dish]
        item_str = f"{dish} — {price}"
        user_baskets.setdefault(user_id, []).append(item_str)
        order_history.setdefault(user_id, []).append(item_str)
        await update.message.reply_photo(meme_url, caption=f"✅ Добавлено в корзину: {item_str}")
    elif text in MENU.get("🥣 Обед", {}).get("Второе", {}):
        dish = text
        price, meme_url = MENU["🥣 Обед"]["Второе"][dish]
        item_str = f"{dish} — {price}"
        user_baskets.setdefault(user_id, []).append(item_str)
        order_history.setdefault(user_id, []).append(item_str)
        await update.message.reply_photo(meme_url, caption=f"✅ Добавлено в корзину: {item_str}")
    else:
        # Поиск блюда в остальных категориях
        found = False
        for cat, dishes in MENU.items():
            if isinstance(dishes, dict):
                for dish, (price, meme_url) in dishes.items():
                    if dish == text:
                        item_str = f"{dish} — {price}"
                        user_baskets.setdefault(user_id, []).append(item_str)
                        order_history.setdefault(user_id, []).append(item_str)
                        await update.message.reply_photo(meme_url, caption=f"✅ Добавлено в корзину: {item_str}")
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
