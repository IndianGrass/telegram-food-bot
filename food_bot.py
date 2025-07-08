import os
import random
import nest_asyncio
import datetime

nest_asyncio.apply()

import asyncio
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ContextTypes, filters, CallbackQueryHandler
)

TOKEN = os.getenv("BOT_TOKEN")

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

user_baskets = {}  # {user_id: [items]}
order_history = {}  # {user_id: {date: [items]}}
user_profiles = {}  # {user_id: {"username": ..., "first_name": ...}}

def get_today():
    return datetime.date.today().isoformat()

def get_main_keyboard():
    return ReplyKeyboardMarkup([
        [KeyboardButton("Старт"), KeyboardButton("Стоп")],
        [KeyboardButton("🧺 Корзина"), KeyboardButton("✅ Подтвердить заказ")],
        [KeyboardButton("🗑️ Очистить корзину"), KeyboardButton("📜 История заказов")],
        [KeyboardButton("🔥 ТОП заказчиков")]
    ], resize_keyboard=True)

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
        # Считаем поцелуи
        for word in price_text.split():
            if "поцел" in word:
                num = ''.join(filter(str.isdigit, word))
                if num.isdigit():
                    kisses += int(num)
        # Считаем обнимашки
        for word in price_text.split():
            if "обним" in word:
                num = ''.join(filter(str.isdigit, word))
                if num.isdigit():
                    hugs += int(num)
    return kisses, hugs

async def send_random_meme(update, item_str):
    memes_folder = "memes"
    try:
        meme_files = [f for f in os.listdir(memes_folder) if f.lower().endswith((".jpg", ".jpeg", ".png"))]
    except FileNotFoundError:
        meme_files = []
    if meme_files:
        meme_path = os.path.join(memes_folder, random.choice(meme_files))
        with open(meme_path, "rb") as photo:
            await update.message.reply_photo(photo, caption=f"✅ Добавлено в корзину: {item_str}")
    else:
        await update.message.reply_text(f"✅ Добавлено в корзину: {item_str}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_profiles[user.id] = {"username": user.username, "first_name": user.first_name}
    await update.message.reply_text("Привет! Нажми 'Старт' чтобы открыть меню.", reply_markup=get_main_keyboard())

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
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
            text_resp += f"\n\n💋 Поцелуйчиков: {kisses}\n🤗 Обнимашек: {hugs}\n\nВы можете удалить блюдо, нажав кнопку ниже."
            keyboard = [[InlineKeyboardButton(f"❌ {i+1}", callback_data=f"del_{i}") for i in range(len(items))]]
            await update.message.reply_text(text_resp, reply_markup=InlineKeyboardMarkup(keyboard))

    elif text == "🗑️ Очистить корзину":
        user_baskets[user_id] = []
        await update.message.reply_text("🗑️ Корзина очищена.")

    elif text == "✅ Подтвердить заказ":
        today = get_today()
        items = user_baskets.get(user_id, [])
        if not items:
            await update.message.reply_text("Корзина пуста. Добавьте что-нибудь.")
        else:
            order_history.setdefault(user_id, {}).setdefault(today, []).extend(items)
            user_baskets[user_id] = []
            await update.message.reply_text("✅ Заказ подтверждён и сохранён в истории!")

    elif text == "📜 История заказов":
        hist = order_history.get(user_id, {})
        if not hist:
            await update.message.reply_text("У вас ещё нет истории заказов.")
        else:
            text_resp = "📜 Ваша история заказов:\n"
            for date, items in hist.items():
                text_resp += f"\n📅 {date}:\n" + "\n".join(f"• {item}" for item in items)
            await update.message.reply_text(text_resp)

    elif text == "🔥 ТОП заказчиков":
        scores = []
        for uid, days in order_history.items():
            all_items = sum(days.values(), [])
            kisses, hugs = count_total(all_items)
            user = user_profiles.get(uid, {})
            name = user.get("username") or user.get("first_name") or f"id{uid}"
            scores.append((name, kisses, hugs))
        scores.sort(key=lambda x: (x[1] + x[2]), reverse=True)
        if not scores:
            await update.message.reply_text("Пока никто не сделал заказов.")
        else:
            resp = "🔥 ТОП заказчиков:\n"
            for i, (name, k, h) in enumerate(scores[:10], 1):
                resp += f"{i}. {name}: 💋 {k}, 🤗 {h}\n"
            await update.message.reply_text(resp)

    # Выбор категории меню
    elif text in MENU.keys():
        if text == "🥣 Обед":
            keyboard = ReplyKeyboardMarkup(
                [[KeyboardButton("Первое")], [KeyboardButton("Второе")], [KeyboardButton("🔙 Назад")]],
                resize_keyboard=True
            )
            await update.message.reply_text("Выберите подкатегорию Обеда:", reply_markup=keyboard)
        else:
            dishes = MENU[text]
            keyboard = submenu_keyboard(dishes)
            await update.message.reply_text(f"Выберите блюдо из категории {text}:", reply_markup=keyboard)

    # Подкатегории обеда
    elif text in ["Первое", "Второе"]:
        dishes = MENU["🥣 Обед"].get(text, {})
        keyboard = submenu_keyboard(dishes)
        await update.message.reply_text(f"Выберите блюдо из раздела {text}:", reply_markup=keyboard)

    # Выбор блюда (учитываем вложенность)
    else:
        found = False
        for cat, dishes in MENU.items():
            if isinstance(dishes, dict):
                # Прямые блюда в категории (Завтрак, Ужин, Полезная еда)
                if all(isinstance(v, tuple) for v in dishes.values()):
                    if text in dishes:
                        price = dishes[text][0]
                        item_str = f"{text} — {price}"
                        user_baskets.setdefault(user_id, []).append(item_str)
                        await send_random_meme(update, item_str)
                        found = True
                        break
                else:
                    # Вложенные подкатегории, например обед
                    for subcat in dishes.values():
                        if isinstance(subcat, dict) and text in subcat:
                            price = subcat[text][0]
                            item_str = f"{text} — {price}"
                            user_baskets.setdefault(user_id, []).append(item_str)
                            await send_random_meme(update, item_str)
                            found = True
                            break
                if found:
                    break
        if not found:
            await update.message.reply_text("❓ Не понял, выберите из меню.")

async def delete_item(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    index = int(query.data.replace("del_", ""))
    if user_id in user_baskets and 0 <= index < len(user_baskets[user_id]):
        removed = user_baskets[user_id].pop(index)
        await query.edit_message_text(f"❌ Удалено из корзины: {removed}")

async def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(delete_item))
    print("🤖 Бот запущен...")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
