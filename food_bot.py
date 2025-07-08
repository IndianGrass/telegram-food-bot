import asyncio
import os
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from telegram.ext import (
    ApplicationBuilder, CommandHandler,
    MessageHandler, ContextTypes, filters
)
from collections import defaultdict
from datetime import datetime

TOKEN = os.getenv("BOT_TOKEN")

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

user_baskets = defaultdict(list)
order_history = defaultdict(list)
users = {}

def category_keyboard():
    keyboard = [[KeyboardButton(cat)] for cat in MENU.keys()]
    keyboard.append([
        KeyboardButton("🧺 Корзина"),
        KeyboardButton("🗑️ Очистить корзину")
    ])
    keyboard.append([
        KeyboardButton("📖 История заказов"), KeyboardButton("✅ Оформить заказ")
    ])
    keyboard.append([
        KeyboardButton("🗑️ Удалить блюдо из корзины"), KeyboardButton("🔝 ТОП заказчиков")
    ])
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def count_total(basket_items):
    kisses, hugs = 0, 0
    for item in basket_items:
        if "поцелуйчик" in item:
            try:
                kisses += int(item.split()[1])
            except:
                pass
        elif "обнимашк" in item:
            try:
                hugs += int(item.split()[1])
            except:
                pass
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

async def show_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    history = order_history.get(user_id, [])
    if not history:
        await update.message.reply_text("📭 У вас нет истории заказов.")
    else:
        text = "📖 История заказов:\n"
        for date, items in history:
            text += f"📅 {date}:\n" + "\n".join(f"• {i}" for i in items) + "\n\n"
        await update.message.reply_text(text)

async def confirm_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    items = user_baskets.get(user_id, [])
    if not items:
        await update.message.reply_text("🧺 Сначала добавьте что-нибудь в корзину!")
        return
    today = datetime.now().strftime("%Y-%m-%d")
    order_history[user_id].append((today, items.copy()))
    user_baskets[user_id] = []
    await update.message.reply_text("✅ Заказ оформлен и сохранён в истории! 📝")

async def delete_item_from_basket(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    basket = user_baskets.get(user_id, [])
    if not basket:
        await update.message.reply_text("🧺 Корзина пуста.")
        return
    keyboard = [[KeyboardButton(item)] for item in basket]
    keyboard.append([KeyboardButton("🔙 Назад")])
    await update.message.reply_text("Выберите, что удалить:", reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))
    context.user_data['delete_mode'] = True

async def show_top_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    stats = []
    for uid, history in order_history.items():
        total_kiss, total_hug = 0, 0
        for _, items in history:
            k, h = count_total(items)
            total_kiss += k
            total_hug += h
        name = users.get(uid, {}).get("username") or users.get(uid, {}).get("first_name") or f"ID {uid}"
        stats.append((name, total_kiss, total_hug))
    if not stats:
        await update.message.reply_text("Пока нет данных для ТОПа.")
        return
    stats.sort(key=lambda x: (x[1], x[2]), reverse=True)
    text = "🔝 ТОП заказчиков:\n"
    for i, (name, kiss, hug) in enumerate(stats, 1):
        text += f"{i}. {name} — 💋 {kiss}, 🤗 {hug}\n"
    await update.message.reply_text(text)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username
    first_name = update.effective_user.first_name
    if user_id not in users:
        users[user_id] = {"username": username, "first_name": first_name}

    text = update.message.text

    if context.user_data.get('delete_mode'):
        context.user_data['delete_mode'] = False
        if text == "🔙 Назад":
            await start(update, context)
            return
        try:
            user_baskets[user_id].remove(text)
            await update.message.reply_text(f"❌ Удалено: {text}", reply_markup=category_keyboard())
        except ValueError:
            await update.message.reply_text("❌ Не удалось удалить. Попробуйте снова.", reply_markup=category_keyboard())
        return

    if text == "🔙 Назад":
        await start(update, context)
    elif text == "🧺 Корзина":
        await basket(update, context)
    elif text == "🗑️ Очистить корзину":
        await clear_basket(update, context)
    elif text == "📖 История заказов":
        await show_history(update, context)
    elif text == "✅ Оформить заказ":
        await confirm_order(update, context)
    elif text == "🗑️ Удалить блюдо из корзины":
        await delete_item_from_basket(update, context)
    elif text == "🔝 ТОП заказчиков":
        await show_top_users(update, context)
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
                user_baskets[user_id].append(f"{text} — {price}")
                await update.message.reply_text(f"✅ Добавлено в корзину: {text} ({price})")
                return
        await update.message.reply_text("❓ Не понял. Выбери из меню.")

async def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("🤖 Бот запущен...")
    await app.run_polling()

if __name__ == "__main__":
    import nest_asyncio
    nest_asyncio.apply()

    loop = asyncio.get_event_loop()
    loop.create_task(main())
    loop.run_forever()

