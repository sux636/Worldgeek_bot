import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, ConversationHandler, MessageHandler, filters
import json
import os

TOKEN = "8587938425:AAHJQLuJJfb8xM5sYqeS9niyZIvgF-C-lSg"
DB_FILE = "users.db"

# Состояния для загрузки фото
PHOTO = 0

TAGS = [
    "#кино", "#музыка", "#путешествия", "#спорт", "#книги", "#аниме", "#игры", "#кулинария", "#фотография", "#танцы",
    "#йога", "#программирование", "#дизайн", "#психология", "#бизнес", "#стартапы", "#крипта", "#искусство", "#театр", "#поэзия",
    "#кошки", "#собаки", "#астрономия", "#настолки", "#косплей", "#тату", "#vegan", "#кофе", "#вино", "#пиво",
    "#горы", "#море", "#скейт", "#сноуборд", "#велосипед", "#авто", "#мото", "#рыбалка", "#охота", "#садоводство",
    "#медитация", "#мемы", "#standup", "#nft", "#ai", "#мода", "#минимализм", "#эзотерика", "#языки", "#корея",
    "#япония", "#скандинавия", "#берлин", "#бордерколли", "#шпиц", "#хаски", "#корги", "#аквариумистика", "#speedcubing",
    "#гитара", "#укулеле", "#винил", "#darkretreat", "#plantbased", "#кроссфит", "#калланетика", "#бокс", "#джиуджитсу"
]

user_data = {}

def save_db():
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(user_data, f, ensure_ascii=False, indent=2)

if os.path.exists(DB_FILE):
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            user_data = json.load(f)
    except:
        user_data = {}

def compatibility(user1_tags, user2_tags):
    if not user1_tags or not user2_tags: return 0
    common = len(set(user1_tags) & set(user2_tags))
    total = len(set(user1_tags) | set(user2_tags))
    return common / total if total > 0 else 0

# ==================== НАЧАЛО ====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("Создать / обновить профиль", callback_data="create_profile")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Привет! Это #worldgeek — знакомства по настоящим интересам\n\n"
        "Сейчас добавим тебе красивое фото и интересы\n"
        "Нажми кнопку ниже ↓",
        reply_markup=reply_markup
    )

async def create_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("Пришли мне своё фото (одно, самое крутое)")
    return PHOTO

async def receive_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    photo_file = update.message.photo[-1].file_id  # берём самое качественное

    # сохраняем фото
    context.user_data[user_id] = context.user_data.get(user_id, {})
    context.user_data[user_id]["photo"] = photo_file

    await update.message.reply_text("Фото принято! Теперь выбери интересы (минимум 3):")

    # показываем теги
    keyboard = []
    row = []
    selected = context.user_data[user_id].get("tags", [])
    for i, tag in enumerate(TAGS):
        text = "✅ " + tag if tag in selected else tag
        row.append(InlineKeyboardButton(text, callback_data=f"tag_{tag}"))
        if (i + 1) % 3 == 0:
            keyboard.append(row)
            row = []
    if row: keyboard.append(row)
    keyboard.append([InlineKeyboardButton("Готово", callback_data="done_tags")])
    await update.message.reply_photo(photo_file, caption="Выбери интересы:", reply_markup=InlineKeyboardMarkup(keyboard))
    return ConversationHandler.END

# ==================== ТЕГИ ====================
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if query.data == "create_profile":
        await create_profile(update, context)
        return

    elif query.data.startswith("tag_"):
        tag = query.data[4:]
        if user_id not in context.user_data:
            context.user_data[user_id] = {"tags": []}
        tags = context.user_data[user_id]["tags"]
        if tag in tags:
            tags.remove(tag)
        else:
            tags.append(tag)

        # перерисовываем
        keyboard = []
        row = []
        for i, t in enumerate(TAGS):
            text = "✅ " + t if t in tags else t
            row.append(InlineKeyboardButton(text, callback_data=f"tag_{t}"))
            if (i + 1) % 3 == 0:
                keyboard.append(row)
                row = []
        if row: keyboard.append(row)
        keyboard.append([InlineKeyboardButton("Готово", callback_data="done_tags")])
        photo_id = context.user_data[user_id].get("photo")
        if photo_id:
            await query.edit_message_caption(caption="Выбери интересы:", reply_markup=InlineKeyboardMarkup(keyboard))
        else:
            await query.edit_message_text("Выбери интересы:", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data == "done_tags":
        tags = context.user_data.get(user_id, {}).get("tags", [])
        photo_id = context.user_data.get(user_id, {}).get("photo")
        if len(tags) < 3:
            await query.answer("Нужно минимум 3 интереса!", show_alert=True)
            return

        user_data[str(user_id)] = {
            "username": query.from_user.username or "",
            "first_name": query.from_user.first_name,
            "tags": tags,
            "photo": photo_id
        }
        save_db()
        await query.edit_message_caption(
            caption=f"Профиль обновлён!\nУ тебя {len(tags)} интересов\n\nПиши /search — найду тебе людей!",
            reply_markup=None
        )
        # очищаем временные данные
        if user_id in context.user_data:
            del context.user_data[user_id]

    # лайки и поиск
    elif query.data == "like":
        # (код лайков остался тот же, просто чуть ниже)

        liker_id = context.user_data.get("current_user")
        liked_id = context.user_data.get("current_profile")
        liker_liked = user_data.get(str(liker_id), {}).get("liked", [])
        if str(liked_id) in liker_liked:
            await query.edit_message_caption(caption="ВЗАИМНЫЙ ЛАЙК!\nНапишите друг другу прямо сейчас ❤️")
            await context.bot.send_message(liked_id, "ВЗАИМНЫЙ ЛАЙК! У вас матч с крутым человеком ❤️")
        else:
            await query.answer("Лайк отправлен ❤️", show_alert=True)

        if str(liker_id) not in user_data:
            user_data[str(liker_id)] = {}
        user_data[str(liker_id)].setdefault("liked", []).append(str(liked_id))
        save_db()

    elif query.data == "next":
        await search(update, context, edit=True)

# ==================== ПОИСК С ФОТО ====================
async def search(update: Update, context: ContextTypes.DEFAULT_TYPE, edit=False):
    user_id = update.callback_query.from_user.id if edit else update.effective_user.id

    if str(user_id) not in user_data or not user_data[str(user_id)].get("tags"):
        await (update.callback_query.edit_message_text if edit else update.message.reply_text)("Сначала создай профиль — /start")
        return

    my_tags = set(user_data[str(user_id)]["tags"])
    candidates = []
    for uid, data in user_data.items():
        if uid == str(user_id): continue
        score = compatibility(my_tags, set(data.get("tags", [])))
        if score > 0:
            candidates.append((score, uid, data))

    if not candidates:
        text = "Пока никого. Ждём новых гиков!"
        await (update.callback_query.edit_message_caption if edit else update.message.reply_text)(text)
        return

    candidates.sort(reverse=True)
    score, found_id, found_data = candidates[0]
    percent = int(score * 100)

    keyboard = [
        [InlineKeyboardButton("Лайк", callback_data="like"),
         InlineKeyboardButton("Дальше", callback_data="next")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    caption = f"Совместимость {percent}%\n\n" \
              f"{found_data['first_name']} @{found_data.get('username', '')}\n" \
              f"Интересы: {', '.join(found_data.get('tags', []))}"

    context.user_data["current_user"] = user_id
    context.user_data["current_profile"] = found_id

    photo_id = found_data.get("photo")
    if photo_id:
        if edit:
            await update.callback_query.edit_message_media(
                media=telegram.InputMediaPhoto(photo_id, caption=caption),
                reply_markup=reply_markup
            )
        else:
            await update.message.reply_photo(photo_id, caption=caption, reply_markup=reply_markup)
    else:
        text = caption
        if edit:
            await update.callback_query.edit_message_caption(caption=text, reply_markup=reply_markup)
        else:
            await update.message.reply_text(text, reply_markup=reply_markup)

# ==================== ЗАПУСК ====================
def main():
    app = Application.builder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(create_profile, pattern="^create_profile$")],
        states={PHOTO: [MessageHandler(filters.PHOTO, receive_photo)]},
        fallbacks=[]
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("search", search))
    app.add_handler(conv_handler)
    app.add_handler(CallbackQueryHandler(button_handler))

    print("Бот @worldgeek_bot работает 24/7 с фотками!")
    app.run_polling()

if __name__ == '__main__':
    main()
